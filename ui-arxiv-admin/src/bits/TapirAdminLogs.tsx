import React from "react";
import {
    useRecordContext,
    Datagrid,
    useListController, ListContextProvider, Pagination
} from "react-admin";
import AdminAuditField from "./AdminAuditField";
import ISODateField from "./ISODateFiled";


export const AdminAuditList: React.FC = () => {
    const record = useRecordContext();
    if (!record) return null;

    const controllerProps = useListController({
        resource: 'tapir_admin_audit',
        filter: { affected_user: record.id },
        sort: { field: 'id', order: 'DESC' },
        perPage: 5,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading audit records.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid rowClick="show" empty={<p><b>No audits for this user</b></p>} size="small"
                      bulkActionButtons={false}
            >
                <ISODateField source="log_date" />
                <AdminAuditField source={"id"} />
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
