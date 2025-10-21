import {Box, Card, Divider, Table, TableCell} from '@mui/material';
import {
    List,
    Datagrid,
    TextField,
    ReferenceField,
    EditButton,
    Edit,
    Create,
    SimpleForm,
    ReferenceInput,
    TextInput,
    useRecordContext,
    EmailField,
    ArrayInput,
    SimpleFormIterator,
    NumberInput,
    BooleanInput,
    CreateButton,
    TopToolbar,
    BooleanField,
    NumberField,
    required,
    minValue,
} from 'react-admin';
import IPv4AddressInput from '../components/IPv4AddressInput';
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";
import CardHeader from "@mui/material/CardHeader";
import DashIcon from "@mui/icons-material/ArrowRightAlt";
import CategoryInput from "../bits/CategoryInput";
import CategoryListInput from "../bits/CategoryListInput";

const endorsementCategoryFilters = [
    <TextInput source="name" label="Search" alwaysOn/>,
];

const EndorsementCategoryListActions = () => (
    <TopToolbar>
        <CreateButton />
    </TopToolbar>
);

export const EndorsementCategoryList = () => (
    <Box maxWidth={"lg"} sx={{margin: '0 auto'}}>
        <ConsoleTitle>Category Level Endorsement Settings</ConsoleTitle>
    <List filters={endorsementCategoryFilters} actions={<EndorsementCategoryListActions />}>
        <Datagrid rowClick={"edit"}>
            <TextField source="id"/>
            <BooleanField source="endorse_all"/>
            <BooleanField source="mods_endorse_all"/>
            <BooleanField source="endorse_email"/>
            <NumberField source="papers_to_endorse"/>
        </Datagrid>
    </List>
    </Box>
);

const EndorsementCategoryTitle = () => {
    const record = useRecordContext();
    return <span>Endorsement Category: {record ? `"${record.id}"` : ''}</span>;
};

const EndorsementCategoryFormFields: React.FC<{isCreate: boolean}> = ({isCreate}) => {
    const labelCellWidth = "14rem";
    console.log("create", isCreate);
    
    return (
        <>
            <Card sx={{width: "100%"}}>
                <CardHeader title={<TextField source={"id"} variant={"h5"}/>}/>

                <Table size="small">
                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Category Name</TableCell>
                        <TableCell>
                            { isCreate ? (
                                <CategoryListInput
                                    source={"id"}
                                    validate={[required()]}
                                />
                            ) : (
                                <TextField source="id" sx={{fontSize: "1.2rem"}} />
                            )}
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Endorse All</TableCell>
                        <TableCell><BooleanInput source="endorse_all" label={""} helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Mods Endorse All</TableCell>
                        <TableCell><BooleanInput source="mods_endorse_all" label={""} helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Endorse by Email Address</TableCell>
                        <TableCell><BooleanInput source="endorse_email" label={""} helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Number of papers to endorse</TableCell>
                        <TableCell>
                            <NumberInput
                                source="papers_to_endorse"
                                helperText="Must be 1 or greater"
                                validate={[required(), minValue(1)]}
                            />
                        </TableCell>
                    </TableRow>

                </Table>
            </Card>
        </>
    );
};

export const EndorsementCategoryAdd = () => (
    <Box width="80%" ml="10%">
    <Create>
        <ConsoleTitle>Add Endorsement Category</ConsoleTitle>
        <SimpleForm>
            <EndorsementCategoryFormFields isCreate={true} />
        </SimpleForm>
    </Create>
    </Box>
);

export const EndorsementCategoryEdit = () => (
    <Box width="80%" ml="10%">
    <Edit title={false} component={"div"}>
        <ConsoleTitle><EndorsementCategoryTitle/></ConsoleTitle>
        <SimpleForm>
            <EndorsementCategoryFormFields isCreate={false} />
        </SimpleForm>
    </Edit>
    </Box>
);