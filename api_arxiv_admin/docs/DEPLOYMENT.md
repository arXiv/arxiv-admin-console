# Deployment Environment Variables

## Environment variables

### Database

This should be in the secret manager.

| Variable | Default | Description                                                       |
|---|---|-------------------------------------------------------------------|
| `CLASSIC_DB_URI` | *(required)* | Read/Write SQLAlchemy connection URI for the arXiv MySQL database |

### Application Behavior

| Variable | Default | Description                                                                                                                                                        |
|---|---|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `TESTING` | *(unset)* | When set, enables testing mode: disables GCP storage, sets root path to `""`, and relaxes auth checks. This is only for the unit test so no need for the Terraform |
| `ADMIN_API_ROOT_PATH` | `/admin-api` | API root path prefix (excluding host). Ignored in testing mode. It will be determined by the deployment policy                                                     |

### URLs and Redirects

| Variable | Default | Description |
|---|---|---|
| `ADMIN_APP_URL` | `http://localhost.arxiv.org:5100/admin-console` | URL of the admin frontend app; added to CORS allowed origins and used as default logout redirect |
| `AAA_LOGIN_REDIRECT_URL` | `http://localhost.arxiv.org:5100/aaa/login` | URL to redirect unauthenticated users for login |
| `AAA_TOKEN_REFRESH_URL` | `http://localhost.arxiv.org:5100/aaa/refresh` | URL used to refresh expired OAuth tokens (WIP) |
| `LOGOUT_REDIRECT_URL` | *(value of `ADMIN_APP_URL`)* | URL to redirect users after logout |

### Authentication and Sessions

| Variable | Default | Description                                                                             |
|---|---|-----------------------------------------------------------------------------------------|
| `JWT_SECRET` | *(unset)* | Secret key used to verify JWT tokens. This is shared by many apps. (modapi for example) |
| `AUTH_SESSION_COOKIE_NAME` | `ARXIVNG_SESSION_ID` | Cookie name for the arXiv NG session. Default should be used for prod                   |
| `CLASSIC_COOKIE_NAME` | `tapir_session` | Cookie name for the legacy Tapir session                                                |
| `TRACKING_COOKIE_NAME` | `tapir_tracking` | Cookie name for Tapir tracking                                                          |
| `CLASSIC_SESSION_HASH` | `classic-secret` | Hash secret for classic Tapir session operations (warning logged if unset)              |
| `SESSION_DURATION` | `36000` | Session duration in seconds (warning logged if unset)                                   |

### PWC (Papers with Code) Integration

This should be in the secret manager.

| Variable | Default | Description |
|---|---|---|
| `PWC_SECRET` | `not-very-secret` | Shared secret for PWC integration |
| `PWC_ARXIV_USER_SECRET` | `not-very-secret` | Shared secret for PWC arXiv user operations |

### Email / SMTP

| Variable | Default | Description                                                                                        |
|---|---|----------------------------------------------------------------------------------------------------|
| `ADMIN_API_SMTP_URL` | `ssmtp://smtp.gmail.com:465?user=smtp-relay@arxiv.org&password=p` | SMTP server URL for sending email. We'd probably not use GCP smtp relay since the quota is too low |

### Moderation API

| Variable | Default | Description                                                                                            |
|---|---|--------------------------------------------------------------------------------------------------------|
| `MODAPI_URL` | `https://services.dev.arxiv.org` | Base URL for the moderation API service. May come from other TF output                                 |
| `MODAPI_MODKEY` | `not-a-modkey` | API key for the moderation API. Very likely come from the secret manager secret that belongs to modapi |

### GCP / Cloud Storage

| Variable | Default | Description |
|---|---|---|
| `GCP_PROJECT` | `<NONE>` | GCP project ID used to initialize the GCS client for document storage. Storage is disabled if unset or `<NONE>` |
| `ARXIV_DOCUMENT_BUCKET_NAME` | `<NONE>` | GCS bucket name for arXiv document storage. Storage is disabled if unset or `<NONE>` |
| `GCP_PROJECT_ID` | `arxiv-development` | GCP project ID passed to the FastAPI app state |
| `GCP_PROJECT_CREDS` | *(unset)* | Path or JSON for GCP service account credentials - ? |
| `GCP_SERVICE_REQUEST_SA` | *(unset)* | GCP service account for service-to-service requests - ? |
| `GCP_SERVICE_REQUEST_ENDPOINT` | `localhost:8080` | Endpoint for GCP service requests - ? |

### Endorser Pool (GCP or CIT)

| Variable | Default | Description                                                                                                                   |
|---|---|-------------------------------------------------------------------------------------------------------------------------------|
| `ADMIN_API_ENDORSER_POOL_OBJECT_URL` | *(unset)* | URL of the endorser pool object. For GCP, GCP Project credentials requires the bucket I/O. This is a file system path on CIT. - ?|

### Internal API

| Variable | Default | Description                                                        |
|---|---|--------------------------------------------------------------------|
| `ADMIN_API_SHARED_SECRET` | `not-very-secret` | Shared secret for internal API authentication. This is a TF output |

### User Actions

This is the links used for the drop down menu in the user portal for the submission management.
It may come from the submission 2.0's base URL

| Variable | Default | Description |
|---|---|---|
| `USER_ACTION_SITE` | `https://dev.arxiv.org` | Base site URL used to construct user action URLs |
| `USER_ACTION_URL_REPLACE` | `{site}/user/{doc_id}/replace` | URL template for paper replace action |
| `USER_ACTION_URL_WITHDRAW` | `{site}/user/{doc_id}/withdraw` | URL template for paper withdraw action |
| `USER_ACTION_URL_CROSS` | `{site}/user/{doc_id}/cross` | URL template for paper cross-list action |
| `USER_ACTION_URL_JREF` | `{site}/user/{doc_id}/jref` | URL template for journal reference action |
| `USER_ACTION_URL_PWC_LINK` | `{site}/user/{doc_id}/pwc_link` | URL template for Papers with Code link action |

### arXiv Check Service

So that the admin can jump to the arXiv Check.

| Variable | Default | Description |
|---|---|---|
| `ARXIV_CHECK_URL` | `https://check.dev.arxiv.org` | Base URL for the arXiv submission check service |

### Access Control

This is a kill switch used for the regular users. On web40 at the moment, no regular user should have access.
This is NOT true once the user portal goes on-line. Things like listing of documents, submission's status comes
from the admin api. IOW, this is turned on on web40. It should be off for elsewhere.

| Variable | Default | Description |
|---|---|---|
| `ENABLE_USER_ACCESS` | *(unset)* | When set, enables user-level access (passed through to app state) |

## NOTE

The backend needs to list the sites used for CORS. I'm not certain it should be parameterized, but I could be wrong.
? - not sure what these values are ... I didn't map anything in the terraform code for them.
