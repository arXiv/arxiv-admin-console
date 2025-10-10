import React from 'react';

import {
    List,
    Datagrid,
    TextInput,
    Filter,
    ReferenceField,
    NumberField, TextField, DateField, NumberInput, EmailField,
} from 'react-admin';

import Box from "@mui/material/Box";
import ConsoleTitle from "../bits/ConsoleTitle";
import CategoryField from "../bits/CategoryField";
import UserNameField from "../bits/UserNameField";
import CategoryListInput from "../bits/CategoryListInput";

const QualifiedEndorserFilter = (props: any) => {
    return (
        <Filter {...props}>
            <CategoryListInput source="category" alwaysOn/>
            <NumberInput source="minimum_count"/>
        </Filter>
    );
};


export const QualifiedEndorserList = () => {
    return (
        <Box sx={{ width: '80%', margin: '0 auto'}}>
            <ConsoleTitle>Qualified Endorsers</ConsoleTitle>
            <List filters={<QualifiedEndorserFilter />}>
            <Datagrid rowClick={false} >
                <ReferenceField source="user_id" reference="users">
                    <UserNameField  />
                </ReferenceField>
                <ReferenceField source="user_id" reference="users" label={"Email"}>
                    <EmailField source={"email"}  />
                </ReferenceField>

                <CategoryField label={"Category"} source="category" sourceCategory="archive" sourceClass="subject_class" />

                <NumberField source="document_count" label={"Qualified Papers"} />
                <ReferenceField source="latest_document_id" reference="documents">
                    <DateField source={"dated"} />
                </ReferenceField>

            </Datagrid>
        </List>
        </Box>
    );
};
