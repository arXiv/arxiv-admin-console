import React from "react";
import { useRecordContext } from "react-admin";
import {paths as adminApi} from '../types/admin-api';
type UserT = adminApi['/v1/users/{user_id}']['get']['responses']['200']['content']['application/json'];

import DeletedIcon from '@mui/icons-material/Delete';
import SuspectIcon from '@mui/icons-material/Dangerous';
import BannedIcon from '@mui/icons-material/RemoveCircle';
import VetoIcon from '@mui/icons-material/ThumbDown';
import Tooltip from "@mui/material/Tooltip";

const UserStatusField: React.FC = () => {
    const record = useRecordContext();

    if (!record) return null;

    const { flag_suspect, flag_banned, flag_deleted, veto_status } = record as UserT;

    return (
        <span>
            {flag_deleted ? <Tooltip title={"Deleted"}><DeletedIcon /></Tooltip> : null}
            {flag_suspect ? <Tooltip title={"Suspected user"}><SuspectIcon /></Tooltip> : null}
            {flag_banned ? <Tooltip title={"Banned"}><BannedIcon /></Tooltip> : null}
            {veto_status != "ok" ? <Tooltip title={veto_status}><VetoIcon/></Tooltip> : null}
        </span>
    );
};

export default UserStatusField;
