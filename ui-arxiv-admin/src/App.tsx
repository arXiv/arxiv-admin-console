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

import {TemplateCreate, TemplateList, TemplateEdit} from './templates';
import { UserList, UserEdit, UserCreate } from './users';
import {EndorsementRequestList, EndorsementRequestCreate, EndorsementRequestEdit, EndorsementRequestShow} from './endorsementRequests';
import { Dashboard } from './Dashboard';
import {createAuthProvider} from './authProvider';
import adminApiDataProvider from './adminApiDataProvider';
import {EndorsementCreate, EndorsementEdit, EndorsementList} from "./endorsements";
import {DocumentCreate, DocumentEdit, DocumentList, DocumentShow} from "./documents";
import {CategoryList, CategoryCreate, CategoryEdit} from "./categories";
import {ModeratorCreate, ModeratorEdit, ModeratorList} from "./moderators";
import {OwnershipRequestEdit, OwnershipRequestList, OwnershipRequestShow} from "./ownershipRequests";
import {RuntimeContext, RuntimeContextProvider} from "./RuntimeContext";
import {SubmissionCreate, SubmissionEdit, SubmissionList, SubmissionShow} from "./submissions";
import {TapirSessionEdit, TapirSessionList} from "./tapirSessions";
import {MembershipInstitutionList} from "./membershipInstitutions";
import {darkTheme, lightTheme} from "./navTheme";

import { defaultTheme, defaultDarkTheme } from 'react-admin';
import Typography from "@mui/material/Typography";

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

const AdminConsole: React.FC = () => {
    const runtimeProps = useContext(RuntimeContext);
    const dataProvider = new adminApiDataProvider(runtimeProps.ADMIN_API_BACKEND_URL);
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

            >
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
                    name="email_templates"
                    list={TemplateList}
                    show={ShowGuesser}
                    icon={EmailIcon}
                    recordRepresentation="short_name"
                    edit={TemplateEdit}
                    create={TemplateCreate}
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
                    show={ShowGuesser}
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
                    name="tapir_sessions"
                    list={TapirSessionList}
                    edit={TapirSessionEdit}
                    show={ShowGuesser}
                    icon={TapirSessionIcon}
                />

                <Resource
                    name="membership_institutions"
                    list={MembershipInstitutionList}
                    edit={EditGuesser}
                    show={ShowGuesser}
                    icon={MembershipInstitutionIcon}
                    recordRepresentation="id"
                />

                <Resource name="endorsement_requests_audit"/>
                <Resource name="ownership_requests_audit"/>
                <Resource name="paper_owners"/>
                <Resource name="paper_owners_user_doc"/>
                <Resource name="demographics"/>
                <Resource name="admin_logs"/>
                <Resource name="submission_categories"/>
                <Resource name="tapir_admin_audit"/>

            </Admin>
        </PingBackend>
    )
}

/*
                <Resource
                    name="membership_institutions"
                    list={MembershipInstitutionList}
                    show={ShowGuesser}
                    icon={MembershipInstitutionIcon}
                    recordRepresentation="id"
                />

 */

const App = () => {
    return (
        <RuntimeContextProvider>
            <AdminConsole />
        </RuntimeContextProvider>
    );
}

export default App;
