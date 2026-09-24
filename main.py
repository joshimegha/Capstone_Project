import csv
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from document_loader import DocumentLoadError, list_documents, load_document
from llm_factory import BASE_DIR, get_llm, load_config
from schemas import CaseSummary
from workflow import CaseWorkflow

logger = logging.getLogger("capstone")

REPORT_FIELDS = [
    "file_name", "processing_status", "error",
    "customer_name", "email", "phone_number", "product_or_service",
    "complaint_category", "is_complaint", "escalation_required",
    "supporting_document_available", "case_status", "recommended_next_action",
]


def setup_logging(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(output_dir / "processing.log", encoding="utf-8"),
        ],
    )
    for noisy in ("httpx", "httpcore", "google", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def prepare_output_dirs(output_dir: Path) -> dict[str, Path]:
    dirs = {
        "structured": output_dir / "structured_data",
        "emails": output_dir / "customer_emails",
        "summaries": output_dir / "case_summaries",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def format_summary(file_name: str, s: CaseSummary) -> str:
    return (
        f"INTERNAL CASE SUMMARY - {file_name}\n"
        f"{'=' * 50}\n"
        f"Case Overview:\n{s.case_overview}\n\n"
        f"Key Issue:\n{s.key_issue}\n\n"
        f"Action Taken:\n{s.action_taken}\n\n"
        f"Current Status:\n{s.current_status}\n\n"
        f"Recommended Next Action:\n{s.recommended_next_action}\n"
    )


def process_file(path: Path, workflow: CaseWorkflow, dirs: dict[str, Path]) -> dict:
    row = {"file_name": path.name, "processing_status": "Failed", "error": ""}
    try:
        text = load_document(path)
        result = workflow.run(path.name, text)

        extracted, summary = result["extracted"], result["summary"]
        (dirs["structured"] / f"{path.stem}.json").write_text(
            extracted.model_dump_json(indent=2), encoding="utf-8")
        (dirs["emails"] / f"{path.stem}_email.txt").write_text(result["email"], encoding="utf-8")
        (dirs["summaries"] / f"{path.stem}_summary.txt").write_text(
            format_summary(path.name, summary), encoding="utf-8")

        row.update(extracted.model_dump(exclude={"issue_description", "resolution_provided"}))
        row["recommended_next_action"] = summary.recommended_next_action
        row["processing_status"] = "Success"
        logger.info("[%s] Completed", path.name)
    except DocumentLoadError as e:
        row["error"] = str(e)
        logger.error("[%s] Load error: %s", path.name, e)
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"
        logger.exception("[%s] Processing error", path.name)
    return row


def write_report(rows: list[dict], report_path: Path) -> None:
    rows = sorted(rows, key=lambda r: r["file_name"])
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    config = load_config()
    data_dir = BASE_DIR / config.get("data_dir", "data")
    output_dir = BASE_DIR / config.get("output_dir", "output")
    setup_logging(output_dir)

    try:
        files = list_documents(data_dir, config.get("supported_extensions", [".txt", ".pdf", ".docx"]))
    except DocumentLoadError as e:
        logger.error(e)
        return
    if not files:
        logger.warning("No eligible documents found in %s", data_dir)
        return

    logger.info("Found %d document(s) using provider '%s'", len(files), config["provider"])
    dirs = prepare_output_dirs(output_dir)
    workflow = CaseWorkflow(get_llm(config))

    start = time.perf_counter()
    rows = []
    with ThreadPoolExecutor(max_workers=config.get("max_workers", 3)) as pool:
        futures = [pool.submit(process_file, f, workflow, dirs) for f in files]
        for fut in as_completed(futures):
            rows.append(fut.result())

    report_path = output_dir / "final_report.csv"
    write_report(rows, report_path)

    ok = sum(r["processing_status"] == "Success" for r in rows)
    logger.info("Done: %d succeeded, %d failed in %.1fs. Report: %s",
                ok, len(rows) - ok, time.perf_counter() - start, report_path)


if __name__ == "__main__":
    main()
