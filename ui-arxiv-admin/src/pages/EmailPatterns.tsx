import {
    List,
    Datagrid,
    TextField,
    EditButton,
    Edit,
    Create,
    SimpleForm,
    TextInput,
    useRecordContext,
    Filter,
    SelectInput,
    useListContext,
    Pagination,
    BulkDeleteButton,
    useDataProvider,
    useNotify,
    useUnselectAll,
    useRefresh
} from 'react-admin';
import { Button } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

const patternPurposeOptions = [
    {id: 'black', name: 'Black'},
    {id: 'block', name: 'Block'},
    {id: 'white', name: 'White'},
];

const EmailPatternFilter = (props: any) => {
    return (
        <Filter {...props}>
            <SelectInput
                label="Purpose"
                source="purpose"
                choices={patternPurposeOptions.slice(1)}
                alwaysOn
                emptyValue={patternPurposeOptions[0].id}
                emptyText={patternPurposeOptions[0].name}
            />
            <TextInput label={"Pattern"} source={"pattern"} alwaysOn/>
        </Filter>
    );
};

// Custom bulk delete button that includes purpose in the path
const EmailPatternBulkDeleteButton = () => {
    const dataProvider = useDataProvider();
    const notify = useNotify();
    const refresh = useRefresh();
    const unselectAll = useUnselectAll('email_patterns');
    const { selectedIds, data } = useListContext();

    const handleClick = async () => {
        if (selectedIds.length > 0 && data) {
            try {
                const purpose = data[0].purpose;
                console.log(`Deleting ${selectedIds.length} email patterns for purpose ${purpose}`);
                // Delete records grouped by purpose
                await dataProvider.deleteMany('email_patterns', {
                    ids: selectedIds,
                    meta: {purpose}
                });
                notify(`${selectedIds.length} email patterns deleted`, {type: 'info'});
            } catch (error) {
                notify('Error deleting email patterns', {type: 'error'});
            }
            unselectAll();
            refresh();
        }
    };

    return (
        <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleClick}
            disabled={selectedIds.length === 0}
            size="small"
        >
            Delete ({selectedIds.length})
        </Button>
    );
};

// Custom pagination with rows per page selector
const EmailPatternPagination = () => <Pagination rowsPerPageOptions={[10, 25, 50, 100]} />;

export const EmailPatternList = () => (
    <List 
        filters={<EmailPatternFilter/>} 
        filterDefaultValues={{purpose: 'black'}}
    >
        <Datagrid rowClick={false} bulkActionButtons={<EmailPatternBulkDeleteButton />}>
            <TextField source="id" label="Pattern" />
        </Datagrid>
    </List>
);

export const EmailPatternCreate = () => (
    <Create>
        <SimpleForm>
            <TextInput source="id" label="Pattern" />
            <SelectInput 
                source="purpose" 
                choices={patternPurposeOptions}
                label="Purpose"
            />
        </SimpleForm>
    </Create>
);
