from logging import getLogger

from arxiv.config import Settings
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Database:

    @staticmethod
    def instance() -> "Database":
        return globals()["_DATABASE_INSTANCE_"]

    def __init__(self, base_settings: Settings):
        self.engine = (
            create_engine(base_settings.CLASSIC_DB_URI,
                               echo=base_settings.ECHO_SQL,
                               isolation_level=base_settings.CLASSIC_DB_TRANSACTION_ISOLATION_LEVEL,
                               pool_recycle=600,
                               max_overflow=(base_settings.REQUEST_CONCURRENCY - 5),
                               # max overflow is how many + base pool size, which is 5 by default
                               pool_pre_ping=base_settings.POOL_PRE_PING))
        if base_settings.LATEXML_DB_URI:
            stmt_timeout: int = max(base_settings.LATEXML_DB_QUERY_TIMEOUT, 1)
            self.latexml_engine = create_engine(base_settings.LATEXML_DB_URI,
                                           connect_args={"options": f"-c statement_timeout={stmt_timeout}s"},
                                           echo=base_settings.ECHO_SQL,
                                           isolation_level=base_settings.LATEXML_DB_TRANSACTION_ISOLATION_LEVEL,
                                           pool_recycle=600,
                                           max_overflow=(base_settings.REQUEST_CONCURRENCY - 5),
                                           pool_pre_ping=base_settings.POOL_PRE_PING)
        else:
            self.latexml_engine = None
        self.session_local = sessionmaker(autocommit=False, autoflush=False)


    def get_session(self):
        """Dependency for fastapi routes"""
        logger = getLogger(__name__)
        # from arxiv.db import _classic_engine
        with self.session_local(bind=self.engine) as session:
            try:
                yield session
                if session.new or session.dirty or session.deleted:
                    session.commit()
            except HTTPException:  # HTTP exception is a normal business
                session.rollback()
                raise
            except Exception as _e:
                logger.warning(f'Commit failed, rolling back', exc_info=True)
                session.rollback()
                raise

    def set_to_global(self) -> None:
        globals()["_DATABASE_INSTANCE_"] = self

    @staticmethod
    def get_from_global() -> "Database":
        return globals()["_DATABASE_INSTANCE_"]



class DatabaseSession:
    """Context manager for managing SQLAlchemy sessions."""

    def __init__(self):
        self.db = Database.get_from_global()
        self.session_generator = self.db.get_session()  # Get the session generator
        self.session = None

    def __enter__(self):
        """Enter the context and retrieve a session."""
        self.session = next(self.session_generator)  # Retrieve the session from generator
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context, commit or rollback session, and ensure cleanup."""
        try:
            next(self.session_generator, None)  # Finalize the session (commit/rollback)
        except StopIteration:
            pass  # Generator is exhausted, nothing to do
