import { Layout } from 'react-admin';
import { AdminConsoleAppBar } from './AdminConsoleAppBar';

export const AdminConsoleLayout = (props: any) => <Layout {...props} appBar={AdminConsoleAppBar} />;
