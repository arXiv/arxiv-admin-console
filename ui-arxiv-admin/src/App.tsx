import {Admin, EditGuesser, Resource, ShowGuesser} from 'react-admin';
import React, {ReactNode, useContext, useEffect, useState, lazy, Suspense} from 'react';

import UserIcon from '@mui/icons-material/Group';
import EmailIcon from '@mui/icons-material/EmailOutlined';
import EndorsedEcon from '@mui/icons-material/Verified';
import RequestIcon from '@mui/icons-material/MeetingRoom';
import DocumentIcon from '@mui/icons-material/Book';
import CategoryIcon from '@mui/icons-material/List';
import ModeratorIcon from '@mui/icons-material/Policy';
import OwnershipRequestIcon from '@mui/icons-material/Star';
import OwnershipIcon from '@mui/icons-material/DoneOutline';
import SubmissionIcon from '@mui/icons-material/Draw';
import TapirSessionIcon from '@mui/icons-material/ConfirmationNumberSharp';
import MembershipInstitutionIcon from '@mui/icons-material/School';
import EmailPatternIcon from '@mui/icons-material/FilterList';
import EndorsementDomainIcon from '@mui/icons-material/Domain';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';


// Lazy load page components
const EmailTemplateCreate = lazy(() => import('./pages/EmailTemplates').then(module => ({ default: module.EmailTemplateCreate })));
const EmailTemplateList = lazy(() => import('./pages/EmailTemplates').then(module => ({ default: module.EmailTemplateList })));
const EmailTemplateEdit = lazy(() => import('./pages/EmailTemplates').then(module => ({ default: module.EmailTemplateEdit })));

const UserList = lazy(() => import('./pages/Users').then(module => ({ default: module.UserList })));
const UserEdit = lazy(() => import('./pages/Users').then(module => ({ default: module.UserEdit })));

const EndorsementRequestList = lazy(() => import('./pages/EndorsementRequests').then(module => ({ default: module.EndorsementRequestList })));
const EndorsementRequestCreate = lazy(() => import('./pages/EndorsementRequests').then(module => ({ default: module.EndorsementRequestCreate })));
const EndorsementRequestEdit = lazy(() => import('./pages/EndorsementRequests').then(module => ({ default: module.EndorsementRequestEdit })));
const EndorsementRequestShow = lazy(() => import('./pages/EndorsementRequests').then(module => ({ default: module.EndorsementRequestShow })));

const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })));

const EndorsementCreate = lazy(() => import('./pages/Endorsements').then(module => ({ default: module.EndorsementCreate })));
const EndorsementEdit = lazy(() => import('./pages/Endorsements').then(module => ({ default: module.EndorsementEdit })));
const EndorsementList = lazy(() => import('./pages/Endorsements').then(module => ({ default: module.EndorsementList })));

const DocumentList = lazy(() => import('./pages/Documents').then(module => ({ default: module.DocumentList })));
const DocumentShow = lazy(() => import('./pages/Documents').then(module => ({ default: module.DocumentShow })));

const CategoryList = lazy(() => import('./pages/Categories').then(module => ({ default: module.CategoryList })));
const CategoryCreate = lazy(() => import('./pages/Categories').then(module => ({ default: module.CategoryCreate })));
const CategoryEdit = lazy(() => import('./pages/Categories').then(module => ({ default: module.CategoryEdit })));

const ModeratorCreate = lazy(() => import('./pages/Moderators').then(module => ({ default: module.ModeratorCreate })));
const ModeratorEdit = lazy(() => import('./pages/Moderators').then(module => ({ default: module.ModeratorEdit })));
const ModeratorList = lazy(() => import('./pages/Moderators').then(module => ({ default: module.ModeratorList })));

const OwnershipRequestEdit = lazy(() => import('./pages/OwnershipRequests').then(module => ({ default: module.OwnershipRequestEdit })));
const OwnershipRequestList = lazy(() => import('./pages/OwnershipRequests').then(module => ({ default: module.OwnershipRequestList })));
const OwnershipRequestShow = lazy(() => import('./pages/OwnershipRequests').then(module => ({ default: module.OwnershipRequestShow })));

const SubmissionEdit = lazy(() => import('./pages/Submissions').then(module => ({ default: module.SubmissionEdit })));
const SubmissionList = lazy(() => import('./pages/Submissions').then(module => ({ default: module.SubmissionList })));
const SubmissionShow = lazy(() => import('./pages/Submissions').then(module => ({ default: module.SubmissionShow })));

const TapirSessionEdit = lazy(() => import('./pages/TapirSessions').then(module => ({ default: module.TapirSessionEdit })));
const TapirSessionList = lazy(() => import('./pages/TapirSessions').then(module => ({ default: module.TapirSessionList })));

const MembershipInstitutionAdd = lazy(() => import('./pages/MembershipInstitutions').then(module => ({ default: module.MembershipInstitutionAdd })));
const MembershipInstitutionEdit = lazy(() => import('./pages/MembershipInstitutions').then(module => ({ default: module.MembershipInstitutionEdit })));
const MembershipInstitutionList = lazy(() => import('./pages/MembershipInstitutions').then(module => ({ default: module.MembershipInstitutionList })));

// Add remaining lazy imports
const OwnershipCreate = lazy(() => import('./pages/Ownerships').then(module => ({ default: module.OwnershipCreate })));
const OwnershipEdit = lazy(() => import('./pages/Ownerships').then(module => ({ default: module.OwnershipEdit })));
const OwnershipList = lazy(() => import('./pages/Ownerships').then(module => ({ default: module.OwnershipList })));

const EmailPatternCreate = lazy(() => import('./pages/EmailPatterns').then(module => ({ default: module.EmailPatternCreate })));
const EmailPatternList = lazy(() => import('./pages/EmailPatterns').then(module => ({ default: module.EmailPatternList })));

const EndorsementDomainAdd = lazy(() => import('./pages/EndorsementDomains').then(module => ({ default: module.EndorsementDomainAdd })));
const EndorsementDomainEdit = lazy(() => import('./pages/EndorsementDomains').then(module => ({ default: module.EndorsementDomainEdit })));
const EndorsementDomainList = lazy(() => import('./pages/EndorsementDomains').then(module => ({ default: module.EndorsementDomainList })));

const MetadataEdit = lazy(() => import('./pages/Metadata').then(module => ({ default: module.MetadataEdit })));

// Keep these as regular imports since they're needed immediately
import {RuntimeContext, RuntimeContextProvider} from "./RuntimeContext";

import {createAuthProvider} from './authProvider';
import adminApiDataProvider from './adminApiDataProvider';
import {darkTheme, lightTheme} from "./navTheme";

import { defaultTheme, defaultDarkTheme, ListGuesser } from 'react-admin';
import Typography from "@mui/material/Typography";
import {AdminConsoleLayout} from "./bits/AdminConsoleLayout";

import { MessageDialogProvider } from './components/MessageDialog';
import {useNavigate, Navigate, useParams} from "react-router-dom";
import {AppBar} from "@mui/material";

const RedirectComponent: React.FC<{to: string}> = ({ to }) => {
    useEffect(() => {
        console.log("to -> " + to);
        window.location.href = to;
    }, [to]);

    return null;
};

const UserShowRedirect = () => {
    const { id } = useParams();
    return <Navigate to={`/users/${id}/edit`} replace />;
};

interface PingBackendProps {
    children: ReactNode;
}

// Custom component to ping the backend periodically
const PingBackend: React.FC<PingBackendProps> = ({ children }) => {
    const runtimeProps = useContext(RuntimeContext);
    const [serverStatus, setServerStatus] = useState<string | null>(null);

    useEffect(() => {
        const pingBackend = async () => {
            try {
                const response = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/v1/ping`);
                if (response.ok) {
                    setServerStatus('Online');
                } else {
                    setServerStatus('Offline');
                }
            } catch (error) {
                console.error('Error pinging the backend:', error);
                setServerStatus('Offline');
            }
        };

        // Ping the backend every some seconds
        const intervalId = setInterval(pingBackend, 1 * 60 * 1000);

        // Cleanup interval on component unmount
        return () => clearInterval(intervalId);
    }, []);

    return (
        <>
            {children}
        </>
    );
};

// WithNavigationLinkPanel removed - LinkPanel functionality has been removed from the app

const AdminConsole: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const dataProvider = new adminApiDataProvider(runtimeProps);
    const authProvider = createAuthProvider(runtimeProps);

    return (
        <PingBackend>
            <Suspense fallback={<div>Loading...</div>}>
                <Admin
                    authProvider={authProvider}
                    dataProvider={dataProvider}
                    dashboard={Dashboard}

                    loginPage={(<RedirectComponent to={`${runtimeProps.AAA_URL}/login?next=${runtimeProps.ADMIN_APP_ROOT}`}/>)}

                    theme={lightTheme}
                    darkTheme={darkTheme}

                    layout={ props => (
                        <MessageDialogProvider>
                            <AdminConsoleLayout {...props} />
                        </MessageDialogProvider>
                    )}
                >
                {/* Your existing resources */}
                <Resource
                    name="users"
                    list={UserList}
                    show={UserShowRedirect}
                    icon={UserIcon}
                    recordRepresentation="name"
                    edit={UserEdit}
                />

                <Resource
                    name="endorsement_requests"
                    list={EndorsementRequestList}
                    show={EndorsementRequestShow}
                    icon={RequestIcon}
                    edit={EndorsementRequestEdit}
                    create={EndorsementRequestCreate}
                    recordRepresentation="id"
                />

                <Resource
                    name="endorsements"
                    list={EndorsementList}
                    show={ShowGuesser}
                    icon={EndorsedEcon}
                    recordRepresentation="name"
                    edit={EndorsementEdit}
                    create={EndorsementCreate}
                />

                <Resource
                    name="ownership_requests"
                    list={OwnershipRequestList}
                    edit={OwnershipRequestEdit}
                    icon={OwnershipRequestIcon}
                    recordRepresentation="id"
                />

                <Resource
                    name="paper_owners"
                    list={OwnershipList}
                    icon={OwnershipIcon}
                />

                <Resource
                    name="submissions"
                    list={SubmissionList}
                    edit={SubmissionEdit}
                    show={SubmissionShow}
                    icon={SubmissionIcon}
                    recordRepresentation="id"
                />

                <Resource
                    name="documents"
                    list={DocumentList}
                    show={DocumentShow}
                    icon={DocumentIcon}
                    recordRepresentation="id"
                />

                <Resource
                    name="categories"
                    list={CategoryList}
                    icon={CategoryIcon}
                    edit={CategoryEdit}
                    create={CategoryCreate}
                    recordRepresentation="id"
                />

                <Resource
                    name="moderators"
                    list={ModeratorList}
                    show={ShowGuesser}
                    icon={ModeratorIcon}
                    edit={ModeratorEdit}
                    create={ModeratorCreate}
                    recordRepresentation="id"
                />

                <Resource
                    name="email_templates"
                    list={EmailTemplateList}
                    icon={EmailIcon}
                    recordRepresentation="short_name"
                    edit={EmailTemplateEdit}
                    create={EmailTemplateCreate}
                />

                <Resource
                    name="tapir_sessions"
                    list={TapirSessionList}
                    edit={TapirSessionEdit}
                    icon={TapirSessionIcon}
                    recordRepresentation="id"
                />

                <Resource
                    name="email_patterns"
                    list={EmailPatternList}
                    icon={EmailPatternIcon}
                    create={EmailPatternCreate}
                />

                <Resource
                    name="membership_institutions"
                    icon={MembershipInstitutionIcon}
                    list={MembershipInstitutionList}
                    edit={MembershipInstitutionEdit}
                    create={MembershipInstitutionAdd}
                />

                <Resource
                    name="endorsement_domains"
                    icon={EndorsementDomainIcon}
                    list={EndorsementDomainList}
                    edit={EndorsementDomainEdit}
                    create={EndorsementDomainAdd}
                />

                <Resource name="endorsement_requests_audit"/>
                <Resource name="ownership_requests_audit"/>
                <Resource name="paper_owners_user_doc"/>
                <Resource name="demographics"/>
                <Resource name="admin_logs"/>
                <Resource name="submission_categories"/>
                <Resource name="tapir_admin_audit"/>
                <Resource name="orcid_ids"/>
                <Resource name="author_ids"/>
                <Resource name="can_submit_to"/>
                <Resource name="can_endorse_for"/>
                <Resource name="metadata"
                          edit={MetadataEdit}
                />
                <Resource name="paper_pw"/>

                </Admin>
            </Suspense>
        </PingBackend>
    )
}

const App = () => {
    return (
        <RuntimeContextProvider>
            <AdminConsole />
        </RuntimeContextProvider>
    );
}

export default App;
