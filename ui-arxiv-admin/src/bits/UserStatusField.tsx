import React from "react";
import {FieldProps, useRecordContext} from "react-admin";
import {paths as adminApi} from '../types/admin-api';
type UserT = adminApi['/v1/users/{user_id}']['get']['responses']['200']['content']['application/json'];

import DeletedIcon from '@mui/icons-material/Delete';
import SuspectIcon from '@mui/icons-material/Dangerous';
import BannedIcon from '@mui/icons-material/RemoveCircle';
import VetoIcon from '@mui/icons-material/FileUploadOff';
import AdminIcon from '@mui/icons-material/AdminPanelSettings';
import SystemIcon from '@mui/icons-material/Settings';
import ModIcon from '@mui/icons-material/Traffic';

import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";

interface UserStatusFieldProps extends FieldProps {
    variant?: string
}

const UserStatusField: React.FC<UserStatusFieldProps> = ({variant}) => {
    const record = useRecordContext();

    if (!record) return null;

    const { flag_suspect, flag_banned, flag_deleted, veto_status, flag_edit_users, flag_edit_system, flag_is_mod } = record as UserT;

    return (
        <span>
            {flag_deleted ? <Tooltip title={"Deleted"}>
                <span>
                    <DeletedIcon />
                    {variant === "labeled" ? (<Typography variant="body2">Deleted</Typography>) : null}
                </span>
            </Tooltip> : null}
            {flag_suspect ? <Tooltip title={"Flagged user"}>
                <span>
                    <SuspectIcon />
                    {variant === "labeled" ? (<Typography variant="body2">Flagged</Typography>) : null}
                </span>
            </Tooltip> : null}
            {flag_banned ? <Tooltip title={"Banned"}>
                <span>
                    <BannedIcon />
                    {variant === "labeled" ? (<Typography variant="body2">Suspended</Typography>) : null}
                </span>
            </Tooltip> : null}
            {veto_status != "ok" ? <Tooltip title={veto_status}>
                <span>
                    <VetoIcon/>
                    {variant === "labeled" ? (<Typography variant="body2">{veto_status}</Typography>) : null}
                </span>
            </Tooltip> : null}
            {flag_edit_users ? <Tooltip title={"Can edit users"}>
                <span>
                <AdminIcon />
                    {variant === "labeled" ? (<Typography variant="body2">{"Admin"}</Typography>) : null}
                </span>
            </Tooltip> : null}
            {flag_edit_system ? <Tooltip title={"Owner"}>
                <span>
                <SystemIcon />
                    {variant === "labeled" ? (<Typography variant="body2">{"Owner"}</Typography>) : null}
                </span>
            </Tooltip> : null}
            {flag_is_mod ? <Tooltip title={"Is moderator"}>
                <span>
                    <ModIcon />
                    {variant === "labeled" ? (<Typography variant="body2">{"Mod"}</Typography>) : null}
                </span>
            </Tooltip> : null}
        </span>
    );
};

export default UserStatusField;
