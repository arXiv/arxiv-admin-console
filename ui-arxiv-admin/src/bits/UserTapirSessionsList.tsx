import React from 'react';
import {
    Datagrid,
    NumberField,
    useRecordContext,
    useListController,
    ListContextProvider,
    Pagination,
} from 'react-admin';
import { useNavigate } from 'react-router-dom';
import ISODateField from './ISODateFiled';

const UserTapirSessionsList: React.FC = () => {
    const record = useRecordContext();
    const navigate = useNavigate();

    if (!record?.id) return null;

    const controllerProps = useListController({
        resource: 'tapir_sessions',
        filter: { user_id: record.id },
        sort: { field: 'id', order: 'DESC' },
        perPage: 5,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading sessions.</p>;

    const handleRowClick = (id: any): false => {
        navigate(`/tapir_sessions/${id}/edit`);
        return false;
    };

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid bulkActionButtons={false} rowClick={handleRowClick}>
                <NumberField source="id" label="Session ID" />
                <ISODateField source="last_reissue" showTime label="Last Reissue" />
                <ISODateField source="start_time" showTime label="Start Time" />
                <ISODateField source="end_time" showTime label="End Time" />
            </Datagrid>
            <Pagination sx={{
                '& .MuiTablePagination-toolbar': {
                    minHeight: '32px',
                    padding: '2px 8px'
                },
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                    fontSize: '0.8rem'
                }
            }} />
        </ListContextProvider>
    );
};

export default UserTapirSessionsList;
