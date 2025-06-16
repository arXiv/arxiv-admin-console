# from pydantic_sqlalchemy_2 import sqlalchemy_to_pydantic
from typing import Type, Container, Optional, Dict, Any

from arxiv.db.models import TapirEmailTemplate, OwnershipRequestsAudit, CrossControl
from pydantic import BaseModel, create_model, ConfigDict
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty


class OrmConfig:
    """Configuration class for ORM models."""
    model_config = ConfigDict(from_attributes=True)


def sqlalchemy_to_pydantic(
        db_model: Type, *, config: Type = OrmConfig, exclude: Container[str] = [], id_key: str = "id"
) -> Type[BaseModel]:
    """
    Convert a SQLAlchemy model to a Pydantic model, compatible with Pydantic v2.
    """
    mapper = inspect(db_model)
    fields: Dict[str, tuple] = {}

    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                name = attr.key
                if name in exclude:
                    continue
                column = attr.columns[0]
                python_type: Optional[type] = None

                if hasattr(column.type, "impl"):
                    if hasattr(column.type.impl, "python_type"):
                        python_type = column.type.impl.python_type
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type

                assert python_type, f"Could not infer python_type for {column}"

                default = None
                if column.default is None and not column.nullable:
                    default = ...

                fields[name] = (python_type, default)

    # Create the Pydantic model with the new Pydantic v2 configuration style
    pydantic_model = create_model(
        db_model.__name__,
        __module__=db_model.__module__,
        **fields,
    )

    # Set the model_config directly on the class
    pydantic_model.model_config = config.model_config if hasattr(config, 'model_config') else ConfigDict(
        from_attributes=True)

    # Add id property
    def id_property(self):
        return getattr(self, id_key)

    setattr(pydantic_model, 'id', property(id_property))

    return pydantic_model


TapirEmailTemplateModel = sqlalchemy_to_pydantic(TapirEmailTemplate)
# _CategoryModel = sqlalchemy_to_pydantic(Category)
#DocumentModel = sqlalchemy_to_pydantic(Document)
#MetadataModel = sqlalchemy_to_pydantic(Metadata)
#PaperPwModel = sqlalchemy_to_pydantic(PaperPw)
#DemographicModel = sqlalchemy_to_pydantic(Demographic)
# EndorsementModel = sqlalchemy_to_pydantic(Endorsement)
# EndorsementRequestModel = sqlalchemy_to_pydantic(EndorsementRequest)
#EndorsementRequestsAuditModel = sqlalchemy_to_pydantic(EndorsementRequestsAudit)

OwnershipRequestsAuditModel = sqlalchemy_to_pydantic(OwnershipRequestsAudit)
#PaperOwnerModel = sqlalchemy_to_pydantic(PaperOwner, id_key="document_id")

# TapirUserModel = sqlalchemy_to_pydantic(TapirUser)

CrossControlModel = sqlalchemy_to_pydantic(CrossControl)

# TapirSessionModel = sqlalchemy_to_pydantic(TapirSession, id_key="session_id")
