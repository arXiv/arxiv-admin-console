import {
    List,
    Datagrid,
    TextField,
    DateField,
    useGetIdentity,
    RaRecord,
    useRecordContext,
    ReferenceField
} from 'react-admin';
import {stringify} from "node:querystring";

const PaperOwnersList : React.FC = ()  => {
    const record = useRecordContext();
    console.log("paper owner list "  + JSON.stringify(record))
    if (!record) return null;
    return (
        <List
            resource="paper_owners"
            title="Paper Ownership"
            perPage={10}
            filter={{ user_id: record.id}}
            sort={{ field: 'id', order: 'DESC' }}
            exporter={false}
            searchable={false}
        >
            <Datagrid rowClick="edit">
                <ReferenceField reference={"documents"} source={"document_id"} >
                    <TextField source="paper_id" />
                </ReferenceField>
                <ReferenceField reference={"documents"} source={"document_id"} >
                    <TextField source="title" />
                </ReferenceField>
                <TextField source="date" />
            </Datagrid>
        </List>
    );
};

export default PaperOwnersList;
