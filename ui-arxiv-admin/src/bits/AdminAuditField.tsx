
import React from 'react';
import {useRecordContext, FieldProps, TextField} from 'react-admin';
import {paths as adminApi} from '../types/admin-api';
import {createAdminAuditEvent} from "../components/AdminAuditEvents";
type TapirAdminAudit = adminApi['/v1/tapir_admin_audit/{id}']['get']['responses']['200']['content']['application/json'];


const AdminAuditField: React.FC<FieldProps> = () => {
    const record = useRecordContext();
    if (!record) return null;
    const adminEvent = createAdminAuditEvent(record);
    return adminEvent.describe();
};

export default AdminAuditField;
