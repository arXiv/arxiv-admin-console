import React from "react";
import { useRecordContext, Datagrid, List, TextField, DateField, useGetOne } from "react-admin";
import { paths as adminApi } from '../types/admin-api';

type UserModel = adminApi['/v1/users/{user_id}']['get']['responses']['200']['content']['application/json'];
type TapirAdminAuditModel = adminApi['/v1/tapir_admin_audit/{id}']['get']['responses']['200']['content']['application/json'];


const paperLink = (docId: string, paperId: string) =>
    `<a href="/auth/admin/paper-detail.php?document_id=${docId}">${paperId}</a>`;

const userLink = (user?: UserModel, fallbackId?: string) =>
    user
        ? `<a href="/users/${user.id}">${user.first_name} ${user.last_name}</a>`
        : fallbackId ?? "unknown user";

export const AdminActionDescriptionField = () => {
    const record = useRecordContext<TapirAdminAuditModel>();
    if (!record) return null;

    // @ts-ignore
    const { data: adminUser, isLoading: loadingAdmin } = useGetOne<UserModel>('users', { id: record.admin_user });
    // @ts-ignore
    const { data: affectedUser, isLoading: loadingAffected } = useGetOne<UserModel>('users', { id: record.affected_user });

    if (loadingAdmin || loadingAffected) return <span>Loading...</span>;

    const admin = userLink(adminUser, record.admin_user);
    const affected = userLink(affectedUser, record.affected_user);

    const { action, data } = record;

    let html: string;

    switch (action) {
        case "add_paper_owner":
            html = `${admin} made ${affected} an owner of paper ${paperLink(data, data)}`;
            break;
        case "add_paper_owner_2":
            html = `${admin} made ${affected} an owner of paper ${paperLink(data, data)} through the process-ownership screen`;
            break;
        case "make_moderator":
            html = `${admin} made ${affected} a moderator of ${data}`;
            break;
        case "unmake_moderator":
            html = `${admin} revoked ${affected} being moderator of ${data}`;
            break;
        case "arXiv_change_status": {
            const match = data.match(/^([^ ]*) -> ([^ ]*)$/);
            if (match) {
                const [, oldStatus, newStatus] = match;
                html = `${admin} moved ${affected} from status ${oldStatus} to ${newStatus}`;
            } else {
                html = `${admin} changed status of ${affected} with data: ${data}`;
            }
            break;
        }
        case "arXiv_make_author":
            html = `${admin} made ${affected} an author of ${paperLink(data, data)}`;
            break;
        case "arXiv_make_nonauthor":
            html = `${admin} made ${affected} a nonauthor of ${paperLink(data, data)}`;
            break;
        case "arXiv_change_paper_pw":
            html = `${admin} changed the paper password for ${paperLink(data, data)} which was submitted by ${affected}`;
            break;
        case "endorsed_by_suspect":
            try {
                const [endorserId, _category, endorsementId] = data.split(" ");
                html = `Automated action: ${affected} was flagged because they <a href="/auth/admin/generic-detail.php?tapir_y=endorsements&tapir_id=${endorsementId}">was endorsed</a> by user ${endorserId} who is also a suspect.`;
            } catch {
                html = "Malformed data in endorsement record.";
            }
            break;
        case "got_negative_endorsement":
            try {
                const [endorserId, category, endorsementId] = data.split(" ");
                html = `Automated action: ${affected} was flagged because they got a <a href="/auth/admin/generic-detail.php?tapir_y=endorsements&tapir_id=${endorsementId}">negative endorsement</a> from user ${endorserId}.`;
            } catch {
                html = "Malformed data in negative endorsement record.";
            }
            break;
        default:
            html = `Unknown action: ${action}`;
    }

    return <span dangerouslySetInnerHTML={{ __html: html }} />;
};


export const AdminAuditList = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <List
            resource="tapir_admin_audit"
            title="Paper Ownership"
            perPage={5}
            filter={{ affected_user: record.id}}
            sort={{ field: 'id', order: 'DESC' }}
            exporter={false}
            empty={<b><p>No admin audit records found</p></b>}
        >
            <Datagrid rowClick="show">
                <DateField source="log_date" />
                <TextField source="admin_user" />
                <TextField source="affected_user" />
                <AdminActionDescriptionField />
            </Datagrid>
        </List>
    );
}

