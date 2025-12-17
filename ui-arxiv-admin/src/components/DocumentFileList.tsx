/*

 */

import {
    useListController,
    ListContextProvider,
    Datagrid,
    Identifier, NumberField, BooleanField,
    Pagination
} from 'react-admin';
import React from 'react';
import StorageURLField from "../bits/StorageURLField";
import DocumentFileTypeField from "../bits/DocumentFileTypeField";
import DocumentFileDownloadField from "../bits/DocumentFileDownloadField";
import DocumentFileUploadField from "../bits/DocumentFileUploadField";


const DocumentFileList: React.FC<{document_id?: Identifier}> = ({document_id}) => {
    if (!document_id) return null;

    const controllerProps = useListController({
        resource: 'document-files',
        filter: { document_id: document_id },
        perPage: 10,
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
                <BooleanField source={"exists"} label="Exists" sortable={false} />
                <DocumentFileTypeField source={"id"} label="Type" sortable={false} />
                <StorageURLField source={"id"} showBucket={true} label={"Storage"} sortable={false} />
                <StorageURLField source={"id"} showPath={true} label={"Path"} sortable={false} />
                <NumberField source={"file_size"} label="Size" sortable={false} />
                <DocumentFileUploadField label="Upload" sortable={false} />
                <DocumentFileDownloadField source={"id"} label="Download" sortable={false} />
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default DocumentFileList;
