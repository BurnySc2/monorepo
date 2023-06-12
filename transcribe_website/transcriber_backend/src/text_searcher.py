"""
For the Telegram downloader, this is a tool to search for text matching a regex pattern from the transcriptions.
"""
import asyncio
import sys
from pathlib import Path

from pony import orm  # pyre-fixme[21]

sys.path.append(str(Path(__file__).parent.parent))

from src.db_telegram import MessageModel  # noqa: E402
from src.db_transcriber import JobItem, OutputResult, db  # noqa: E402
from src.secrets_loader import SECRETS as SECRETS_FULL  # noqa: E402

SECRETS = SECRETS_FULL.TextSearcher


async def glob_search(
    glob_pattern: str,
    allowed_languages: list[str],
) -> list[str]:
    """
    'abc' LIKE 'abc'    true
    'abc' LIKE 'a%'     true
    'abc' LIKE '_b_'    true
    'abc' LIKE 'c'      false
    """
    case_sensitive_str = "LIKE" if SECRETS.case_sensitive else "ILIKE"
    results = []
    with orm.db_session():
        # https://www.postgresql.org/docs/current/functions-matching.html#FUNCTIONS-LIKE
        if allowed_languages:
            matching_file_names = orm.select(
                # pyre-fixme[16]
                j.local_file for j in JobItem for o in OutputResult
                if j == o.job_item and orm.raw_sql(f"o.txt_original {case_sensitive_str} '{glob_pattern}'")
            )
        else:
            matching_file_names = orm.select(
                j.local_file for j in JobItem for o in OutputResult if (
                    j == o.job_item and o.detected_language in allowed_languages
                    and orm.raw_sql(f"o.txt_original {case_sensitive_str} '{glob_pattern}'")
                )
            )
            # Filter by language
        statement = matching_file_names.get_sql()
        matching_file_names = db.execute(statement)
        matching_file_names_results: list[str] = [i[0] for i in matching_file_names]
        matching_messages: list[MessageModel] = orm.select(
            # pyre-fixme[16]
            m for m in MessageModel if m.downloaded_file_path in matching_file_names_results
        )
        for message in matching_messages:
            message: MessageModel  # pyre-fixme[35]
            results.append([message.downloaded_file_path, message.link])
    return results


async def regex_search(regex_pattern: str, allowed_languages: list[str]) -> list[str]:
    # https://www.postgresql.org/docs/current/functions-matching.html#FUNCTIONS-POSIX-REGEXP
    results = []
    with orm.db_session():
        matching_file_names: list[str] = orm.select(
            # pyre-fixme[16]
            j.local_file for j in JobItem for o in OutputResult
            if j == o.job_item and orm.raw_sql(f"o.txt_original ~ '{regex_pattern}'")
        )
        matching_file_names_results: list[str] = list(matching_file_names)
        # TODO Find in text file - if exists, find in SRT file and find the context (one line before)
        # where in the video/audio it happened
        matching_messages: list[MessageModel] = orm.select(
            # pyre-fixme[16]
            m for m in MessageModel if m.downloaded_file_path in matching_file_names_results
        )
        for message in matching_messages:
            message: MessageModel  # pyre-fixme[35]
            results.append([message.downloaded_file_path, message.link])
    return results


async def main():
    if SECRETS.glob_pattern:
        results = await glob_search(SECRETS.glob_pattern, allowed_languages=SECRETS.allowed_languages)
    else:
        results = await regex_search(SECRETS.regex_pattern, allowed_languages=SECRETS.allowed_languages)
    for result in results:
        # print(result)
        sys.stdout.write(f"{result}\n")


if __name__ == "__main__":
    asyncio.run(main())
