import {useMediaQuery} from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
    SortPayload,
    NumberInput,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    useListContext, SelectInput, EditButton
} from 'react-admin';

// import { addDays } from 'date-fns';

import React, {useContext}  from "react";
import CategoryField from "../bits/CategoryField";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import {RuntimeContext} from "../RuntimeContext"; // for "Become This User"


/*
    archive: Mapped[str] = mapped_column(ForeignKey('arXiv_archives.archive_id'), primary_key=True, nullable=False, server_default=FetchedValue())
    subject_class: Mapped[str] = mapped_column(String(16), primary_key=True, nullable=False, server_default=FetchedValue())
    definitive: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    active: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    category_name: Mapped[Optional[str]]
    endorse_all: Mapped[Literal['y', 'n', 'd']] = mapped_column(Enum('y', 'n', 'd'), nullable=False, server_default=text("'d'"))
    endorse_email: Mapped[Literal['y', 'n', 'd']] = mapped_column(Enum('y', 'n', 'd'), nullable=False, server_default=text("'d'"))
    papers_to_endorse: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'0'"))
    endorsement_domain: Mapped[Optional[str]] = mapped_column(ForeignKey('arXiv_endorsement_domains.endorsement_domain'), index=True)
 */


const CategoryFilter = (props: any) => {
    const {setFilters, filterValues} = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setFilters({
            ...filterValues,
        });
    };

    return (
        <Filter {...props}>
            <TextInput label="Primary" source="archive" alwaysOn/>
            <TextInput label="Subject class" source="subject_class" alwaysOn/>
            <BooleanInput label="Active" source="active"/>
        </Filter>
    );
};


const yesNoDefaultChoices = [
    {id: 'y', name: 'Yes'},
    {id: 'n', name: 'No'},
    {id: 'd', name: 'Default'},
];


export const CategoryList = () => {
    const sorter: SortPayload = {field: 'archive', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <Box maxWidth={"xl"} sx={{margin: '0 auto'}}>
            <ConsoleTitle>Categories</ConsoleTitle>
            <List filters={<CategoryFilter/>}>
                {isSmall ? (
                    <SimpleList
                        primaryText={record => record.archive}
                        secondaryText={record => record.subject_class}
                        tertiaryText={record => record.category_name}
                    />
                ) : (
                    <Datagrid rowClick={false} sort={sorter} bulkActionButtons={false}>
                        <CategoryField sourceCategory="archive" sourceClass="subject_class" source="archive"
                                       label={"Category"}/>
                        <TextField source="category_name"/>
                        <BooleanField source="active" FalseIcon={null}/>
                        <BooleanField source="definitive" FalseIcon={null}/>
                        <EditButton/>
                    </Datagrid>
                )}
            </List>
        </Box>
    );
};


const CategoryTitle = () => {
    const record = useRecordContext();
    return <span>Category {record ? `"${record.archive}.${record.subject_class || '*'}" - ${record.category_name}` : ''}</span>;
};

export const CategoryEdit = () => {
    const runtimeProps = useContext(RuntimeContext);
    const isOwner = runtimeProps.currentUser;

    return (
    <Box width="80%" ml="10%">

        <Edit title={<CategoryTitle/>} component={"div"}>
            <ConsoleTitle><CategoryTitle/></ConsoleTitle>
            <Paper>
                <SimpleForm>
                    <TextInput source="archive"/>
                    <TextInput source="subject_class"/>

                    <BooleanField source="definitive" FalseIcon={null}/>
                    <BooleanField source="active" FalseIcon={null}/>
                    <TextInput source="category_name"/>

                    <SelectInput source="endorse_all" label="Endorse All" choices={yesNoDefaultChoices}/>
                    <SelectInput source="endorse_email" label="Endorse Email" choices={yesNoDefaultChoices}/>

                    <NumberInput source="papers_to_endorse"/>
                    <TextInput source="endorsement_domain"/>
                </SimpleForm>
            </Paper>
        </Edit>
    </Box>
    )
}

export const CategoryCreate = () => (
    <Create>
        <SimpleForm>
            <TextInput source="archive"/>

            <TextInput source="subject_class"/>
        </SimpleForm>
    </Create>
);


