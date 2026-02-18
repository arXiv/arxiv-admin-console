"""Database compatibility helpers for cross-database support.

This module provides utilities to handle differences between MySQL and SQLite,
allowing the codebase to work with both databases without MySQL-specific code.
"""

from typing import Any, TYPE_CHECKING, Union, cast as type_cast
from sqlalchemy import cast, func, LargeBinary
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.orm.attributes import InstrumentedAttribute

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_dialect_name(session: 'Session') -> str:
    """Get the name of the current database dialect.

    Args:
        session: SQLAlchemy session

    Returns:
        Dialect name (e.g., 'mysql', 'sqlite')
    """
    return session.bind.dialect.name if session.bind else 'unknown'


def cast_for_encoding(column: Union[ColumnElement[Any], InstrumentedAttribute[Any]], session: 'Session') -> ColumnElement[Any]:
    """Conditionally cast a column to LargeBinary for MySQL latin1 encoding.

    MySQL stores text in latin1 encoding in some legacy arXiv tables, which requires
    casting to LargeBinary for LIKE operations with non-ASCII characters. SQLite
    doesn't need this casting.

    Args:
        column: The column to potentially cast
        session: SQLAlchemy session to determine dialect

    Returns:
        Cast column for MySQL, original column for other databases

    Example:
        >>> # Instead of: cast(TapirUser.first_name, LargeBinary).like(...)
        >>> # Use: cast_for_encoding(TapirUser.first_name, session).like(...)
    """
    dialect = get_dialect_name(session)
    if dialect == 'mysql':
        return cast(column, LargeBinary)
    return type_cast(ColumnElement[Any], column)


def from_unixtime_compat(column: Union[ColumnElement[Any], InstrumentedAttribute[Any]], session: 'Session') -> ColumnElement[Any]:
    """Database-agnostic conversion from unix timestamp to datetime.

    MySQL uses FROM_UNIXTIME(), SQLite uses datetime(col, 'unixepoch').

    Args:
        column: The column containing a unix timestamp
        session: SQLAlchemy session to determine dialect

    Returns:
        Appropriate datetime conversion expression for the current dialect
    """
    dialect = get_dialect_name(session)
    if dialect == 'sqlite':
        return func.datetime(column, 'unixepoch')
    # MySQL and others: FROM_UNIXTIME
    return func.from_unixtime(column)


def group_concat_compat(column: Union[ColumnElement[Any], InstrumentedAttribute[Any]], session: 'Session',
                        separator: str = ',') -> ColumnElement[Any]:
    """Database-agnostic string aggregation function.

    MySQL uses GROUP_CONCAT, SQLite uses group_concat, PostgreSQL uses string_agg.
    This function provides a unified interface.

    Args:
        column: The column to aggregate
        session: SQLAlchemy session to determine dialect
        separator: String separator for concatenation (default: ',')

    Returns:
        Appropriate aggregation function for the current dialect

    Example:
        >>> # Instead of: func.group_concat(User.name)
        >>> # Use: group_concat_compat(User.name, session)
    """
    dialect = get_dialect_name(session)

    if dialect in ('mysql', 'sqlite'):
        # Both MySQL and SQLite use group_concat
        return func.group_concat(column, separator)
    elif dialect == 'postgresql':
        # PostgreSQL uses string_agg
        return func.string_agg(column, separator)
    else:
        # Fallback to group_concat
        return func.group_concat(column, separator)
