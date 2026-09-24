import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

from prompts import EMAIL_PROMPT, EXTRACTION_PROMPT, SUMMARY_PROMPT
from schemas import CaseExtraction, CaseSummary

logger = logging.getLogger(__name__)


class CaseWorkflow:
    """Step 1: Document -> Extraction. Step 2 (parallel): Extraction -> Email + Summary."""

    def __init__(self, llm, retries: int = 2):
        self.extraction_chain = (
            EXTRACTION_PROMPT | llm.with_structured_output(CaseExtraction)
        ).with_retry(stop_after_attempt=retries)

        email_chain = (EMAIL_PROMPT | llm | StrOutputParser()).with_retry(stop_after_attempt=retries)
        summary_chain = (
            SUMMARY_PROMPT | llm.with_structured_output(CaseSummary)
        ).with_retry(stop_after_attempt=retries)

        self.generation_chain = RunnableParallel(email=email_chain, summary=summary_chain)

    def run(self, name: str, document: str) -> dict:
        logger.info("[%s] Step 1: structured extraction", name)
        extracted: CaseExtraction = self.extraction_chain.invoke({"document": document})
        if extracted is None:
            raise ValueError("LLM returned no structured extraction")

        logger.info("[%s] Step 2: generating email and case summary in parallel", name)
        generated = self.generation_chain.invoke({
            "document": document,
            "extracted": extracted.model_dump_json(indent=2),
        })
        if generated["summary"] is None:
            raise ValueError("LLM returned no case summary")

        return {
            "extracted": extracted,
            "email": generated["email"].strip(),
            "summary": generated["summary"],
        }
