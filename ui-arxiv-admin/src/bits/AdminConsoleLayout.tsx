import { Layout } from 'react-admin';
import { AdminConsoleAppBar } from '../components/AdminConsoleAppBar';
import { RightSidebarLayout } from './RightSidebarLayout';

export const AdminConsoleLayout = (props: any) => (
    <RightSidebarLayout {...props} appBar={AdminConsoleAppBar} />
);
