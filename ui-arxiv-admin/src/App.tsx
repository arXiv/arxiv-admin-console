import {Admin, EditGuesser, Resource, ShowGuesser} from 'react-admin';
import React, {ReactNode, useContext, useEffect, useState} from 'react';

import UserIcon from '@mui/icons-material/Group';
import EmailIcon from '@mui/icons-material/EmailOutlined';
import EndorsedEcon from '@mui/icons-material/Verified';
import RequestIcon from '@mui/icons-material/MeetingRoom';
import DocumentIcon from '@mui/icons-material/Book';
import CategoryIcon from '@mui/icons-material/List';
import ModeratorIcon from '@mui/icons-material/Policy';
import OwnershipRequestIcon from '@mui/icons-material/Star';
import SubmissionIcon from '@mui/icons-material/Draw';
import TapirSessionIcon from '@mui/icons-material/ConfirmationNumberSharp';
import MembershipInstitutionIcon from '@mui/icons-material/School';

import {TemplateCreate, TemplateList, TemplateEdit} from './pages/Templates';
import { UserList, UserEdit, UserCreate } from './pages/Users';
import {EndorsementRequestList, EndorsementRequestCreate, EndorsementRequestEdit, EndorsementRequestShow} from './pages/EndorsementRequests';
import { Dashboard } from './pages/Dashboard';
import {createAuthProvider} from './authProvider';
import adminApiDataProvider from './adminApiDataProvider';
import {EndorsementCreate, EndorsementEdit, EndorsementList} from "./pages/Endorsements";
import {DocumentCreate, DocumentEdit, DocumentList, DocumentShow} from "./pages/Documents";
import {CategoryList, CategoryCreate, CategoryEdit} from "./pages/Categories";
import {ModeratorCreate, ModeratorEdit, ModeratorList} from "./pages/Moderators";
import {OwnershipRequestEdit, OwnershipRequestList, OwnershipRequestShow} from "./pages/OwnershipRequests";
import {RuntimeContext, RuntimeContextProvider} from "./RuntimeContext";
import {SubmissionCreate, SubmissionEdit, SubmissionList, SubmissionShow} from "./pages/Submissions";
import {TapirSessionEdit, TapirSessionList} from "./pages/TapirSessions";
import {MembershipInstitutionList} from "./pages/MembershipInstitutions";
import {darkTheme, lightTheme} from "./navTheme";

import { defaultTheme, defaultDarkTheme, ListGuesser } from 'react-admin';
import Typography from "@mui/material/Typography";
import {OwnershipCreate, OwnershipEdit, OwnershipList} from "./pages/Ownerships";
import {AdminConsoleLayout} from "./bits/AdminConsoleLayout";

// Import the new sliding panel components
import { SlidingPanelProvider } from './SlidingPanelContext';
import { LinkPanel } from './components/LinkPanel';
import { PanelToggleButton } from './components/PanelToggleButton';
import { PersistentDrawerLayout } from './components/PersistentDrawerLayout';
import {useNavigate} from "react-router-dom";

const RedirectComponent: React.FC<{to: string}> = ({ to }) => {
    useEffect(() => {
        console.log("to -> " + to);
        window.location.href = to;
    }, [to]);

    return null;
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
                const response = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/ping`);
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

// Create the wrapper component with navigation
const WithNavigationLinkPanel: React.FC = () => {
    const navigate = useNavigate();
    return <LinkPanel onNavigate={navigate} />;
};

const AdminConsole: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const dataProvider = new adminApiDataProvider(
        runtimeProps.ADMIN_API_BACKEND_URL,
        runtimeProps.AAA_URL
    );
    const authProvider = createAuthProvider(runtimeProps);

    return (
        <PingBackend>
            <Admin
                authProvider={authProvider}
                dataProvider={dataProvider}
                dashboard={Dashboard}

                loginPage={(<RedirectComponent to={`${runtimeProps.AAA_URL}/login?next=${runtimeProps.ADMIN_APP_ROOT}`}/>)}

                theme={lightTheme}
                darkTheme={darkTheme}

                layout={ props => (
                    <PersistentDrawerLayout  panel={<WithNavigationLinkPanel />}>
                        <AdminConsoleLayout {...props} />
                    </PersistentDrawerLayout>
                )}
            >
                {/* Your existing resources */}
                <Resource
                    name="users"
                    list={UserList}
                    show={ShowGuesser}
                    icon={UserIcon}
                    recordRepresentation="name"
                    edit={UserEdit}
                    create={UserCreate}
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
                    name="endorsement_requests"
                    list={EndorsementRequestList}
                    show={EndorsementRequestShow}
                    icon={RequestIcon}
                    edit={EndorsementRequestEdit}
                    create={EndorsementRequestCreate}
                    recordRepresentation="id"
                />

                <Resource
                    name="ownership_requests"
                    list={OwnershipRequestList}
                    edit={OwnershipRequestEdit}
                    icon={OwnershipRequestIcon}
                    recordRepresentation="id"
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
                    edit={DocumentEdit}
                    create={DocumentCreate}
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
                    list={TemplateList}
                    show={ShowGuesser}
                    icon={EmailIcon}
                    recordRepresentation="short_name"
                    edit={TemplateEdit}
                    create={TemplateCreate}
                />

                <Resource
                    name="tapir_sessions"
                    list={TapirSessionList}
                    show={ShowGuesser}
                    icon={TapirSessionIcon}
                    recordRepresentation="id"
                />

                <Resource name="paper_owners" />
                <Resource name="membership_institutions" />
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

            </Admin>
        </PingBackend>
    )
}

const App = () => {
    return (
        <RuntimeContextProvider>
            <SlidingPanelProvider>
                <AdminConsole />
            </SlidingPanelProvider>
        </RuntimeContextProvider>
    );
}

export default App;
