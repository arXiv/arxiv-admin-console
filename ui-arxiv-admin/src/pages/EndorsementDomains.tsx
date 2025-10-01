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
} from 'react-admin';
import IPv4AddressInput from '../components/IPv4AddressInput';
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";
import CardHeader from "@mui/material/CardHeader";
import DashIcon from "@mui/icons-material/ArrowRightAlt";

const endorsementDomainFilters = [
    <TextInput source="name" label="Search" alwaysOn/>,
];

const EndorsementDomainListActions = () => (
    <TopToolbar>
        <CreateButton />
    </TopToolbar>
);

export const EndorsementDomainList = () => (
    <Box maxWidth={"lg"} sx={{margin: '0 auto'}}>
        <ConsoleTitle>Endorsement Domains</ConsoleTitle>
    <List filters={endorsementDomainFilters} actions={<EndorsementDomainListActions />}>
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

const EndorsementDomainTitle = () => {
    const record = useRecordContext();
    return <span>Endorsement Domain: {record ? `"${record.id}"` : ''}</span>;
};

const EndorsementDomainFormFields: React.FC<{isCreate: boolean}> = ({isCreate}) => {
    const labelCellWidth = "10rem";
    console.log("create", isCreate);
    
    return (
        <>
            <Card sx={{width: "100%"}}>
                <CardHeader title={<TextField source={"id"} variant={"h5"}/>}/>

                <Table size="small">
                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Domain Name</TableCell>
                        <TableCell>
                            { isCreate ? <TextInput source="id" /> : <TextField source="id" sx={{fontSize: "1.2rem"}} />}
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>endorse_all</TableCell>
                        <TableCell><BooleanInput source="endorse_all"  helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>mods_endorse_all</TableCell>
                        <TableCell><BooleanInput source="mods_endorse_all"  helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>endorse_email</TableCell>
                        <TableCell><BooleanInput source="endorse_email"  helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>papers_to_endorse</TableCell>
                        <TableCell><NumberInput source="papers_to_endorse"  helperText={false}/></TableCell>
                    </TableRow>

                </Table>
            </Card>
        </>
    );
};

export const EndorsementDomainAdd = () => (
    <Box width="80%" ml="10%">
    <Create>
        <ConsoleTitle>Add Endorsement Domain</ConsoleTitle>
        <SimpleForm>
            <EndorsementDomainFormFields isCreate={true} />
        </SimpleForm>
    </Create>
    </Box>
);

export const EndorsementDomainEdit = () => (
    <Box width="80%" ml="10%">
    <Edit title={false} component={"div"}>
        <ConsoleTitle><EndorsementDomainTitle/></ConsoleTitle>
        <SimpleForm>
            <EndorsementDomainFormFields isCreate={false} />
        </SimpleForm>
    </Edit>
    </Box>
);