import {
    useListController,
    ListContextProvider,
    Datagrid,
    TextField,
    DateField,
    useRecordContext,
    ReferenceField,
    Pagination,
} from 'react-admin';
import React from 'react';

const PaperOwnersList: React.FC = () => {
    const record = useRecordContext();
    if (!record) return null;

    const controllerProps = useListController({
        resource: 'paper_owners',
        filter: { user_id: record.id },
        sort: { field: 'id', order: 'DESC' },
        perPage: 10,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading paper ownership data.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid rowClick="edit">
                <ReferenceField reference="documents" source="document_id" label="arXiv ID">
                    <TextField source="paper_id" />
                </ReferenceField>
                <ReferenceField
                    reference="documents"
                    source="document_id"
                    label="Title"
                    link={(record, reference) => `https://arxiv.org/pdf/${record.paper_id}`}
                >
                    <TextField source="title" />
                </ReferenceField>
                <ReferenceField reference="documents" source="document_id" label="Dated" link={false}>
                    <DateField source="dated" />
                </ReferenceField>
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default PaperOwnersList;
