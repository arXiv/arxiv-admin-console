import React from "react";
import { useRecordContext } from "react-admin";
import Tooltip from "@mui/material/Tooltip";

const UserNameField: React.FC = () => {
    const record = useRecordContext();

    if (!record) return null;

    const { first_name, last_name, username, email, id } = record;

    return (
        <Tooltip title={`${username} <${email}> (${id})`} arrow>
            <span>
                {first_name} {last_name}
            </span>
        </Tooltip>
    );
};

export default UserNameField;
