import {
    List,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
    SortPayload,
    TextInput,
    Filter,
    useRecordContext,
    Identifier,
} from 'react-admin';

import DoDisturbOnIcon from '@mui/icons-material/DoDisturbOn';
import React, { useState, useCallback } from "react";
import PersonNameField from "../bits/PersonNameField";
import Checkbox from '@mui/material/Checkbox';

import {paths as adminApi} from '../types/admin-api';
import ISODateField from "../bits/ISODateFiled";
type UsersT = adminApi['/v1/users/']['get']['responses']['200']['content']['application/json'];


interface UserChooserListProps {
    onUsersSelected?: (selectedUsers: UsersT) => void;
}


const UserChooserFilter = (props: any) => (
    <Filter {...props}>
        <TextInput label="First name" source="first_name" alwaysOn />
        <TextInput label="Last Name" source="last_name" alwaysOn />
        <TextInput label="Login name" source="username" alwaysOn />
        <TextInput label="Search by Email" source="email" alwaysOn />
    </Filter>
);


const UserChooserList = ({ onUsersSelected }: UserChooserListProps) => {
    const sorter: SortPayload = {field: 'user_id', order: 'ASC'};
    const [selectedUsers, setSelectedUsers] = useState<any[]>([]);
    const [selectedIds, setSelectedIds] = useState<Set<Identifier>>(new Set());

    const handleUserSelect = useCallback((user: any, isSelected: boolean) => {
        const newSelectedIds = new Set(selectedIds);
        let newSelectedUsers = [...selectedUsers];

        if (isSelected) {
            newSelectedIds.add(user.id);
            newSelectedUsers.push(user);
        } else {
            newSelectedIds.delete(user.id);
            newSelectedUsers = newSelectedUsers.filter(u => u.id !== user.id);
        }

        setSelectedIds(newSelectedIds);
        setSelectedUsers(newSelectedUsers);

        // Call the callback function with selected users
        if (onUsersSelected) {
            onUsersSelected(newSelectedUsers);
        }
    }, [selectedIds, selectedUsers, onUsersSelected]);

    const SelectCheckbox = () => {
        const record = useRecordContext();
        if (!record) return null;
        return (
            <Checkbox
                checked={selectedIds.has(record.id)}
                onChange={(event) => handleUserSelect(record, event.target.checked)}
                size="small"
            />
        );
    };

    return (
        <List filters={<UserChooserFilter/>} resource="users" actions={false}>
            <Datagrid rowClick={false} sort={sorter} bulkActionButtons={false}>
                <SelectCheckbox />
                <PersonNameField source={"id"} label="Name" />
                <TextField source="username" label={"Login name"}/>
                <EmailField source="email"/>
                <ISODateField source="joined_date" />
                <BooleanField source="flag_edit_users" label={"Admin"} FalseIcon={null}/>
                <BooleanField source="flag_is_mod" label={"Mod"} FalseIcon={null}/>
                <BooleanField source="flag_banned" label={"Suspended"} FalseIcon={null}
                              TrueIcon={DoDisturbOnIcon}/>
                <BooleanField source="flag_suspect" label={"Suspect"} FalseIcon={null}
                              TrueIcon={DoDisturbOnIcon}/>
            </Datagrid>
        </List>
    );
};

export default UserChooserList;
