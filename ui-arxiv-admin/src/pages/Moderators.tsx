import {useMediaQuery} from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    SortPayload,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    ReferenceField,
    useListContext,
    AutocompleteInput,
    useGetOne
} from 'react-admin';

import {addDays} from 'date-fns';

import React from "react";
import CategoryField from "../bits/CategoryField";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";
import ArchiveSubjectClassInput from "../bits/ArchiveSubjectClassInput";
import CategoryInput from "../bits/CategoryInput";
/*
    id: str
    user_id: int
    archive: str
    subject_class: Optional[str]
    is_public: bool
    no_email: bool
    no_web_email: bool
    no_reply_to: bool
    daily_update: bool
 */


const ModeratorFilter = (props: any) => {
    const {setFilters, filterValues} = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setFilters({
            ...filterValues,
        });
    };

    return (
        <Filter {...props}>
            <TextInput label="Archive" source="archive" alwaysOn/>
            <TextInput label="Subject" source="subject_class" alwaysOn/>
            <TextInput label="Last name" source="last_name" alwaysOn/>
            <TextInput label="First name" source="first_name" alwaysOn/>
            <TextInput label="Email" source="email" alwaysOn/>
        </Filter>
    );
};


export const ModeratorList = () => {
    const sorter: SortPayload = {field: 'id', order: 'ASC'};
    return (
        <Box maxWidth={"lg"} sx={{margin: '0 auto'}}>
            <ConsoleTitle>Moderators</ConsoleTitle>
            <List filters={<ModeratorFilter/>} >
                <Datagrid rowClick="edit" sort={sorter}>
                    <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id"
                                   label="Category"/>

                    <ReferenceField source="user_id" reference="users" label={"Moderator"}
                                    link={(record, reference) => `/${reference}/${record.id}`}>
                        <TextField source={"last_name"}/>
                        {", "}
                        <TextField source={"first_name"}/>
                        {" ("}
                        <TextField source={"id"}/>
                        {")"}
                    </ReferenceField>

                    <ReferenceField source="user_id" reference="users" label={"Email"}
                                    link={(record, reference) => `/${reference}/${record.id}`}>
                        <EmailField source={"email"}/>
                    </ReferenceField>

                </Datagrid>
            </List>
        </Box>
    );
};


const ModeratorEditTitle = () => {
    const record = useRecordContext();
    const { data: user, isLoading } = useGetOne(
        'users',
        { id: record?.user_id },
        { enabled: !!record?.user_id }
    );

    if (!record) return <span>Moderator</span>;
    if (isLoading) return <span>Loading...</span>;

    const userName = user ? `${user.first_name} ${user.last_name}` : 'User';
    const category = record.subject_class
        ? `${record.archive}.${record.subject_class}`
        : record.archive;

    return <span>{userName} for {category}</span>;
};

export const ModeratorEdit = () => (
    <Box maxWidth={"md"} sx={{margin: '0 auto'}} >
    <Edit component={"div"}>
        <ConsoleTitle>
            <ModeratorEditTitle />
        </ConsoleTitle>

        <SimpleForm>
            <ReferenceField source="user_id" reference="users" label={"User"}
                            link={(record, reference) => `/${reference}/${record.id}`}>
                <TextField source={"last_name"}/>
                {", "}
                <TextField source={"first_name"}/>
            </ReferenceField>

            <TextInput source="archive"/>
            <TextInput source="subject_class"/>

            <BooleanInput source="is_public" label={"Public"}/>
            <BooleanInput source="no_email" label={"No Email"}/>
            <BooleanInput source="no_web_email" label={"No Web Email"}/>
            <BooleanInput source="no_reply_to" label={"No Reply-To"}/>
            <BooleanInput source="daily_update" label={"Daily Update"}/>
        </SimpleForm>
    </Edit>
    </Box>
);

export const ModeratorCreate = () => (
    <Create>
        <ConsoleTitle>Add Moderator</ConsoleTitle>
        <SimpleForm>
            <ReferenceInput source="user_id" reference="users">
                <AutocompleteInput
                    optionText={(record) => `${record.last_name}, ${record.first_name} (${record.email}) ${record.id}`}
                />
            </ReferenceInput>

            <ArchiveSubjectClassInput source={'id'} label={'Category'} sourceCategory={'archive'}
                                      sourceClass={'subject_class'}/>

            <BooleanInput source="is_public" label={"Public"}/>
            <BooleanInput source="no_email" label={"No Email"}/>
            <BooleanInput source="no_web_email" label={"No Web Mail"}/>
            <BooleanInput source="no_reply_to" label={"No Reply-To"}/>
            <BooleanInput source="daily_update" label={"Daily Update"}/>

        </SimpleForm>
    </Create>
);


