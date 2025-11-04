/*

 */

import {
    useListController,
    ListContextProvider,
    Datagrid,
    TextField,
    ReferenceField,
    Pagination,
    Identifier, NumberField,
} from 'react-admin';
import React from 'react';
import UserNameField from "./UserNameField";
import ISODateField from "./ISODateFiled";


const DocumentFileList: React.FC<{document_id?: Identifier}> = ({document_id}) => {
    if (!document_id) return null;

    const controllerProps = useListController({
        resource: 'document-files',
        filter: { document_id: document_id },
        perPage: 5,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading paper ownership data.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid
                bulkActionButtons={false}
                rowClick={false}
                empty={<p><b>No document files found</b></p>}
            >
                <TextField source={"id"} />
                <TextField source={"file_name"} />
                <NumberField source={"file_size"} />
                <TextField source={"content_type"} />
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default DocumentFileList;
