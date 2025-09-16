from typing import Optional
from pydantic import BaseModel
from enum import Enum

class ArxivNavAppType(str, Enum):
    not_applicable = "not_applicable"
    internal = "internal"
    external = "external"


class ArxivNavItem(BaseModel):
    id: str
    title: str
    url: str
    app: ArxivNavAppType
    active: bool = True
    icon: Optional[str] = None
    items: Optional[list['ArxivNavItem']] = None


arxiv_nav_links: list[ArxivNavItem] = [
    ArxivNavItem(
        id="resources",
        title="Resources",
        url="",
        app=ArxivNavAppType.not_applicable,
        items=[
            ArxivNavItem(
                id="internal_pages",
                title="Internal Pages",
                url="",
                app=ArxivNavAppType.not_applicable,
                items=[
                    ArxivNavItem(
                        id="arxiv_home",
                        title="arXiv Home",
                        url="https://arxiv.org",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="eust_confluence",
                        title="EUST Confluence",
                        url="https://arxiv-org.atlassian.net/wiki/spaces/CMT/overview",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="policy_documentation",
                        title="Policy Documentation",
                        url="https://arxiv-org.atlassian.net/wiki/spaces/APP/overview",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="project_work",
                        title="Project Work",
                        url="https://arxiv-org.atlassian.net/jira/core/projects/ET/board",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="category_taxonomy",
                        title="Category Taxonomy",
                        url="https://arxiv.org/category_taxonomy",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="activity_dashboards",
                        title="Activity Dashboards",
                        url="https://activity.dev.arxiv.org/",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="mod_list",
                        title="Mod List",
                        url="https://dev.arxiv.org/auth/admin/view-moderators.php",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="github_repositories",
                        title="GitHub Repositories",
                        url="https://github.com/orgs/arXiv/teams/administrators/repositories",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="moderator_hub",
                        title="Moderator Hub",
                        url="https://arxiv-org.atlassian.net/wiki/spaces/CMT/pages/640450562/Volunteer+Management+Support",
                        app=ArxivNavAppType.external
                    )
                ]
            ),
            ArxivNavItem(
                id="public_pages",
                title="Public Pages",
                url="",
                app=ArxivNavAppType.not_applicable,
                items=[
                    ArxivNavItem(
                        id="submit",
                        title="Submit",
                        url="https://info.arxiv.org/help/submit",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="registration",
                        title="Registration",
                        url="https://info.arxiv.org/help/registerhelp",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="metadata",
                        title="Metadata",
                        url="https://info.arxiv.org/help/prep",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="tex_accents",
                        title="TeX Accents",
                        url="https://info.arxiv.org/help/prep.html#accents",
                        app=ArxivNavAppType.external
                    ),
                    ArxivNavItem(
                        id="endorsement",
                        title="Endorsement",
                        url="https://info.arxiv.org/help/endorsement",
                        app=ArxivNavAppType.external
                    )
                ]
            )
        ]
    ),
    ArxivNavItem(
        id="submission",
        title="Submission",
        url="",
        app=ArxivNavAppType.not_applicable,
        items=[
            ArxivNavItem(
                id="arxiv_check",
                title="arXiv Check",
                url="http://localhost:3000/",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="overlap_form",
                title="Overlap Form",
                url="https://dev.services.arxiv.org/compare/form",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="sandbox_report",
                title="Sandbox Report",
                url="http://localhost:8000/reports/sandbox-extended",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="legacy_metadata_report",
                title="Legacy Metadata Report",
                url="https://dev.arxiv.org/admin/report",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="ithenticate",
                title="iThenticate",
                url="https://arxiv.turnitin.com/home/",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="mathjax",
                title="Mathjax",
                url="https://math.meta.stackexchange.com/questions/5020/mathjax-basic-tutorial-and-quick-reference",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="deep_l_translator",
                title="Deep L Translator",
                url="https://www.deepl.com/en/translator",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="fastly_purge",
                title="Fastly Purge",
                url="https://arxiv-org.atlassian.net/wiki/x/CADNI",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="google_indexing",
                title="Google Indexing",
                url="https://search.google.com/search-console/welcome",
                app=ArxivNavAppType.external
            )
        ]
    ),
    ArxivNavItem(
        id="user_support",
        title="User Support",
        url="",
        app=ArxivNavAppType.not_applicable,
        items=[
            ArxivNavItem(
                id="tixhelp",
                title="TixHelp",
                url="https://arxiv-org.atlassian.net/jira/servicedesk/projects/AH/queues/custom/15",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="tixmod",
                title="TixMod",
                url="https://arxiv-org.atlassian.net/jira/servicedesk/projects/MOD/queues/custom/16",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="mod_appeals",
                title="Mod Appeals",
                url="https://arxiv-org.atlassian.net/jira/servicedesk/projects/IMAPPEALS/queues/custom/54",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="customer_portal_view",
                title="Customer Portal View",
                url="https://arxiv-org.atlassian.net/servicedesk/customer/portals",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="canned_messages",
                title="Canned Messages",
                url="https://arxiv-org.atlassian.net/plugins/servlet/ac/com.spartez.jira.plugins.commenttemplates/templates-canned-responses?s=com.spartez.jira.plugins.commenttemplates__templates-canned-responses",
                app=ArxivNavAppType.external
            )
        ]
    ),
    ArxivNavItem(
        id="students",
        title="Students",
        url="",
        app=ArxivNavAppType.not_applicable,
        items=[
            ArxivNavItem(
                id="student_dashboard",
                title="Student Dashboard",
                url="https://arxiv-org.atlassian.net/wiki/x/hgF7Tw",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="freeze_metadata_report",
                title="Freeze Metadata Report",
                url="https://dev.arxiv.org/admin/report",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="sandbox_report_students",
                title="Sandbox Report",
                url="http://localhost:8000/reports/sandbox-extended",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="tex_accents_students",
                title="TeX Accents",
                url="https://info.arxiv.org/help/prep.html#accents",
                app=ArxivNavAppType.external
            ),
            ArxivNavItem(
                id="ownership_requests",
                title="Ownership Requests",
                url="https://dev.arxiv.org/auth/admin/list?tapir_y=arXiv-ownership-requests&tapir_f0=workflow_status&tapir_r0=1&tapir_v0=pending&tapir_o0=-request_id",
                app=ArxivNavAppType.external
            )
        ]
    )
]

