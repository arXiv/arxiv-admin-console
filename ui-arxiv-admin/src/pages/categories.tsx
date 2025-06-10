import { useMediaQuery } from '@mui/material';
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
    DateField,
    ReferenceField,
    NumberField,
    DateInput, useListContext, SelectInput, EditButton
} from 'react-admin';

import { addDays } from 'date-fns';

import React from "react";
import CategoryField from "../bits/CategoryField";

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
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setFilters({
            ...filterValues,
        });
    };

    return (
        <Filter {...props}>
            <TextInput label="Primary" source="archive" alwaysOn />
            <TextInput label="Subject class" source="subject_class" alwaysOn/>
            <BooleanInput label="Active" source="active" />
        </Filter>
    );
};


const yesNoDefaultChoices = [
    { id: 'y', name: 'Yes' },
    { id: 'n', name: 'No' },
    { id: 'd', name: 'Default' },
];



export const CategoryList = () => {
    const sorter: SortPayload = {field: 'archive', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List filters={<CategoryFilter />}>
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.archive}
                    secondaryText={record => record.subject_class}
                    tertiaryText={record => record.category_name}
                />
            ) : (
                <Datagrid rowClick={false}  sort={sorter} >
                    <CategoryField sourceCategory="archive" sourceClass="subject_class" source="archive" label={"Category"} />
                    <TextField source="category_name" />
                    <BooleanField source="active" FalseIcon={null}/>
                    <BooleanField source="definitive" FalseIcon={null}/>
                    <EditButton />
                </Datagrid>
            )}
        </List>
    );
};


const CategoryTitle = () => {
    const record = useRecordContext();
    return <span>Category {record ? `"${record.archive}.${record.subject_class || '*'}" - ${record.category_name}` : ''}</span>;
};

export const CategoryEdit = () => (
    <Edit title={<CategoryTitle />}>
        <SimpleForm>
            <TextInput source="archive" />
            <TextInput source="subject_class" />

            <BooleanField source="definitive" FalseIcon={null}/>
            <BooleanField source="active" FalseIcon={null}/>
            <TextInput source="category_name" />

            <SelectInput source="endorse_all" label="Endorse All" choices={yesNoDefaultChoices} />
            <SelectInput source="endorse_email" label="Endorse Email" choices={yesNoDefaultChoices} />

            <NumberInput source="papers_to_endorse" />
            <TextInput source="endorsement_domain" />


        </SimpleForm>
    </Edit>
);

export const CategoryCreate = () => (
    <Create>
        <SimpleForm>
            <TextInput source="archive" />

            <TextInput source="subject_class" />
        </SimpleForm>
    </Create>
);


