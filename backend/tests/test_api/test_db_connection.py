import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_db_connection(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_tables_exist(db_session: AsyncSession):
    result = await db_session.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
    )
    tables = {row[0] for row in result}
    expected = {
        "repositories",
        "repository_files",
        "comparisons",
        "comparison_method_results",
        "comparison_file_matches",
        "comparison_configs",
    }
    assert expected.issubset(tables)
