import React from "react";
import {
    useRecordContext,
    Datagrid,
    TextField,
    DateField,
    useGetOne,
    useListController, ListContextProvider, Pagination, ReferenceField
} from "react-admin";
import { paths as adminApi } from '../types/admin-api';
import UserNameField from './UserNameField';

type UserModel = adminApi['/v1/users/{user_id}']['get']['responses']['200']['content']['application/json'];
type TapirAdminAuditModel = adminApi['/v1/tapir_admin_audit/{id}']['get']['responses']['200']['content']['application/json'];
type TapirAdminAuditAction = TapirAdminAuditModel['action'];


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

    const admin = record.admin_user ? userLink(adminUser, String(record.admin_user)) : "";
    const affected = userLink(affectedUser, String(record.affected_user));

    const { action , data } = record;

    let html: string;

    switch (action as TapirAdminAuditAction) {
        case "add-paper-owner":
            html = `${admin} made ${affected} an owner of paper ${paperLink(data, data)}`;
            break;
        case "add-paper-owner-2":
            html = `${admin} made ${affected} an owner of paper ${paperLink(data, data)} through the process-ownership screen`;
            break;
        case "make-moderator":
            html = `${admin} made ${affected} a moderator of ${data}`;
            break;
        case "unmake-moderator":
            html = `${admin} revoked ${affected} being moderator of ${data}`;
            break;
        case "arXiv-change-status": {
            const match = data.match(/^([^ ]*) -> ([^ ]*)$/);
            if (match) {
                const [, oldStatus, newStatus] = match;
                html = `${admin} moved ${affected} from status ${oldStatus} to ${newStatus}`;
            } else {
                html = `${admin} changed status of ${affected} with data: ${data}`;
            }
            break;
        }
        case "arXiv-make-author":
            html = `${admin} made ${affected} an author of ${paperLink(data, data)}`;
            break;
        case "arXiv-make-nonauthor":
            html = `${admin} made ${affected} a nonauthor of ${paperLink(data, data)}`;
            break;
        case "arXiv-change-paper-pw":
            html = `${admin} changed the paper password for ${paperLink(data, data)} which was submitted by ${affected}`;
            break;
        case "endorsed-by-suspect":
            try {
                const [endorserId, _category, endorsementId] = data.split(" ");
                html = `Automated action: ${affected} was flagged because they <a href="/auth/admin/generic-detail.php?tapir_y=endorsements&tapir_id=${endorsementId}">was endorsed</a> by user ${endorserId} who is also a suspect.`;
            } catch {
                html = "Malformed data in endorsement record. " + data;
            }
            break;
        case "got-negative-endorsement":
            try {
                const [endorserId, _category, endorsementId] = data.split(" ");
                html = `Automated action: ${affected} was flagged because they got a <a href="/auth/admin/generic-detail.php?tapir_y=endorsements&tapir_id=${endorsementId}">negative endorsement</a> from user ${endorserId}.`;
            } catch {
                html = "Malformed data in negative endorsement record. " + data;
            }
            break;

        case "flip-flag":
            try {
                const [flag_name, value] = data.split("=");
                html = `${admin} set ${flag_name} to ${value}.`;
            } catch {
                html = "Malformed data in flip-flag data. " + data;
            }
            break;

        case "become-user":
            html = `Action: ${action} : data ${data}`;
            break;

        case "suspend-user":
            html = `Action: ${action} : data ${data}`;
            break

        case "unsuspend-user":
            html = `Action: ${action} : data ${data}`;
            break;

        case "change-email":
            html = `Action: ${action} : data ${data}`;
            break;

        case "revoke-paper-owner":
            html = `Action: ${action} : data ${data}`;
            break;

        case "change-paper-pw":
            html = `Action: ${action} : data ${data}`;
            break;

        case "change-password":
            html = `Action: ${action} : data ${data}`;
            break;

        case "arXiv-revoke-paper-owner":
            html = `Action: ${action} : data ${data}`;
            break;

        case "arXiv-unrevoke-paper-owner":
            html = `Action: ${action} : data ${data}`;
            break;

        case "add-comment":
            html = `Comment: ${record.comment}`;
            break;

        default:
            html = `Unknown action: ${action} : data ${data}`;
    }

    return <span dangerouslySetInnerHTML={{ __html: html }} />;
};



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
            <Datagrid rowClick="show" empty={<p><b>No audits for this user</b></p>}>
                <DateField source="log_date" />
                <ReferenceField reference={"users"} source={"admin_user"} >
                    <UserNameField />
                </ReferenceField>
                <ReferenceField reference={"users"} source={"affected_user"} >
                    <UserNameField />
                </ReferenceField>
                <AdminActionDescriptionField />
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};
