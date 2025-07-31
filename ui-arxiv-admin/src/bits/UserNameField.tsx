import React from "react";
import {FieldProps, useRecordContext } from "react-admin";
import Tooltip from "@mui/material/Tooltip";

interface UserNameFieldProps {
    withEmail?: boolean;
    withUsername?: boolean;
}

const UserNameField: React.FC<UserNameFieldProps> = ({withEmail, withUsername}) => {
    const record = useRecordContext();

    if (!record) return null;

    const { first_name, last_name, username, email, id } = record;

    return (
        <Tooltip title={`${username} <${email}> (${id})`} arrow>
            <span>
                {first_name} {last_name}
                {withEmail && email ? ` <${email}>` : ""}
                {withUsername && username ? ` (${username})` : ""}
            </span>
        </Tooltip>
    );
};

export default UserNameField;
