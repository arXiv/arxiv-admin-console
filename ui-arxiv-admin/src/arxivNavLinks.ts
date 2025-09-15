export interface ArxivNavLink {
    title: string;
    url: string;
    app: string;
}

export interface ArxivNavLinkSection {
    [categoryName: string]: ArxivNavLink[] | {
        [subCategoryName: string]: ArxivNavLink[];
    };
}

export type ArxivNavLinks = ArxivNavLinkSection[];

export const defaultArxivNavLinks: ArxivNavLinks = [
    {
        "Resources": {
            "Internal Pages": [
                {
                    "title": "arXiv Home",
                    "url": "https://arxiv.org",
                    "app": "external"
                },
                {
                    "title": "EUST Confluence",
                    "url": "https://arxiv-org.atlassian.net/wiki/spaces/CMT/overview",
                    "app": "external"
                },
                {
                    "title": "Policy Documentation",
                    "url": "https://arxiv-org.atlassian.net/wiki/spaces/APP/overview",
                    "app": "external"
                },
                {
                    "title": "Project Work",
                    "url": "https://arxiv-org.atlassian.net/jira/core/projects/ET/board",
                    "app": "external"
                },
                {
                    "title": "Category Taxonomy",
                    "url": "https://arxiv.org/category_taxonomy",
                    "app": "external"
                },
                {
                    "title": "Activity Dashboards",
                    "url": "https://activity.dev.arxiv.org/",
                    "app": "external"
                },
                {
                    "title": "Mod List",
                    "url": "https://dev.arxiv.org/auth/admin/view-moderators.php",
                    "app": "external"
                },
                {
                    "title": "GitHub Repositories",
                    "url": "https://github.com/orgs/arXiv/teams/administrators/repositories",
                    "app": "external"
                },
                {
                    "title": "Moderator Hub",
                    "url": "https://arxiv-org.atlassian.net/wiki/spaces/CMT/pages/640450562/Volunteer+Management+Support",
                    "app": "external"
                }
            ],
            "Public Pages": [
                {
                    "title": "Submit",
                    "url": "https://info.arxiv.org/help/submit",
                    "app": "external"
                },
                {
                    "title": "Registration",
                    "url": "https://info.arxiv.org/help/registerhelp",
                    "app": "external"
                },
                {
                    "title": "Metadata",
                    "url": "https://info.arxiv.org/help/prep",
                    "app": "external"
                },
                {
                    "title": "TeX Accents",
                    "url": "https://info.arxiv.org/help/prep.html#accents",
                    "app": "external"
                },
                {
                    "title": "Endorsement",
                    "url": "https://info.arxiv.org/help/endorsement",
                    "app": "external"
                }
            ]
        }
    },
    {
        "Submission": [
            {
                "title": "arXiv Check",
                "url": "http://localhost:3000/",
                "app": "Check"
            },
            {
                "title": "Overlap Form",
                "url": "https://dev.services.arxiv.org/compare/form",
                "app": "external"
            },
            {
                "title": "Sandbox Report",
                "url": "http://localhost:8000/reports/sandbox-extended",
                "app": "external"
            },
            {
                "title": "Legacy Metadata Report",
                "url": "https://dev.arxiv.org/admin/report",
                "app": "external"
            },
            {
                "title": "iThenticate",
                "url": "https://arxiv.turnitin.com/home/",
                "app": "external"
            },
            {
                "title": "Mathjax",
                "url": "https://math.meta.stackexchange.com/questions/5020/mathjax-basic-tutorial-and-quick-reference",
                "app": "external"
            },
            {
                "title": "Deep L Translator",
                "url": "https://www.deepl.com/en/translator",
                "app": "external"
            },
            {
                "title": "Fastly Purge",
                "url": "https://arxiv-org.atlassian.net/wiki/x/CADNI",
                "app": "external"
            },
            {
                "title": "Google Indexing",
                "url": "https://search.google.com/search-console/welcome",
                "app": "external"
            }
        ]
    },
    {
        "User Support": [
            {
                "title": "TixHelp",
                "url": "https://arxiv-org.atlassian.net/jira/servicedesk/projects/AH/queues/custom/15",
                "app": "external"
            },
            {
                "title": "TixMod",
                "url": "https://arxiv-org.atlassian.net/jira/servicedesk/projects/MOD/queues/custom/16",
                "app": "external"
            },
            {
                "title": "Mod Appeals",
                "url": "https://arxiv-org.atlassian.net/jira/servicedesk/projects/IMAPPEALS/queues/custom/54",
                "app": "external"
            },
            {
                "title": "Customer Portal View",
                "url": "https://arxiv-org.atlassian.net/servicedesk/customer/portals",
                "app": "external"
            },
            {
                "title": "Canned Messages",
                "url": "https://arxiv-org.atlassian.net/plugins/servlet/ac/com.spartez.jira.plugins.commenttemplates/templates-canned-responses?s=com.spartez.jira.plugins.commenttemplates__templates-canned-responses",
                "app": "external"
            }
        ]
    },
    {
        "Students": [
            {
                "title": "Student Dashboard",
                "url": "https://arxiv-org.atlassian.net/wiki/x/hgF7Tw",
                "app": "external"
            },
            {
                "title": "Freeze Metadata Report",
                "url": "https://dev.arxiv.org/admin/report",
                "app": "external"
            },
            {
                "title": "Sandbox Report",
                "url": "http://localhost:8000/reports/sandbox-extended",
                "app": "external"
            },
            {
                "title": "TeX Accents",
                "url": "https://info.arxiv.org/help/prep.html#accents",
                "app": "external"
            },
            {
                "title": "Ownership Requests",
                "url": "https://dev.arxiv.org/auth/admin/list?tapir_y=arXiv-ownership-requests&tapir_f0=workflow_status&tapir_r0=1&tapir_v0=pending&tapir_o0=-request_id",
                "app": "external"
            }
        ]
    }
];
