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
    useRecordContext, EmailField, ArrayInput, SimpleFormIterator, NumberInput, BooleanInput, CreateButton, TopToolbar,
} from 'react-admin';
import IPv4AddressInput from '../components/IPv4AddressInput';
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";
import CardHeader from "@mui/material/CardHeader";
import DashIcon from "@mui/icons-material/ArrowRightAlt";

const membershipInstitutionFilters = [
    <TextInput source="name" label="Search" alwaysOn/>,
];

const MembershipInstitutionListActions = () => (
    <TopToolbar>
        <CreateButton />
    </TopToolbar>
);

export const MembershipInstitutionList = () => (
    <Box maxWidth={"lg"} sx={{margin: '0 auto'}}>
        <ConsoleTitle>Membership Institutions</ConsoleTitle>
        <List filters={membershipInstitutionFilters} actions={<MembershipInstitutionListActions />}>
            <Datagrid rowClick={"edit"}>
                <TextField source="name"/>
                <TextField source="note"/>
                <EmailField source="email"/>
                <TextField source="contact_name"/>
            </Datagrid>
        </List>
    </Box>
);

const MembershipInstitutionTitle = () => {
    const record = useRecordContext();
    return <span>{record ? record.name : ''}</span>;
};

const MembershipInstitutionFormFields = () => {
    const labelCellWidth = "10rem";
    
    return (
        <Box gap={2} sx={{width: "100%"}}>
            <Card >
                <CardHeader title={<TextField source={"name"} variant={"h5"}/>}/>

                <Table size="small">
                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Institution Name</TableCell>
                        <TableCell><TextInput source="name" helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Display Name</TableCell>
                        <TableCell><TextInput source="label"  helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Contact Name</TableCell>
                        <TableCell><TextInput source="contact_name"  helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Contact Email</TableCell>
                        <TableCell><TextInput source="email"  helperText={false}/></TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Note</TableCell>
                        <TableCell><TextInput source="note"  helperText={false} multiline rows={6}/></TableCell>
                    </TableRow>
                </Table>
            </Card>
            <Card sx={{my: 2}}>
                <CardHeader title={"Open URL"}/>

                <Table size="small" >

                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Resolver URL</TableCell>
                        <TableCell><TextInput source="resolver_URL"  helperText={false}/></TableCell>
                    </TableRow>
                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Link Icon</TableCell>
                        <TableCell><TextInput source="link_icon"  helperText={false}/></TableCell>
                    </TableRow>
                    <TableRow>
                        <TableCell sx={{ width: labelCellWidth, textAlign: "right" }}>Alt Text</TableCell>
                        <TableCell><TextInput source="alt_text" helperText={false}/></TableCell>
                    </TableRow>

                </Table>
            </Card>
            <Card>
                <CardHeader title={"IP Addresses and Ranges"}/>

                <ArrayInput source="ip_ranges">
                    <SimpleFormIterator>
                        <Box sx={{display: "flex", flexDirection: "row"}} alignItems={"baseline"} mx={1} my={0} >
                            <IPv4AddressInput source="start" label="Start IP" sx={{width: "14rem"}}/>
                            <DashIcon />
                            <IPv4AddressInput source="end" label="End IP" sx={{width: "14rem"}}/>
                        </Box>
                    </SimpleFormIterator>
                </ArrayInput>
            </Card>
        </Box>
    );
};

export const MembershipInstitutionAdd = () => (
    <Box width="80%" ml="10%">
    <Create>
        <SimpleForm>
            <MembershipInstitutionFormFields />
        </SimpleForm>
    </Create>
    </Box>
);

export const MembershipInstitutionEdit = () => (
    <Box width="80%" ml="10%">
        <Edit title={false} component={"div"}>
            <ConsoleTitle><span>Edit Membership - </span><MembershipInstitutionTitle /></ConsoleTitle>
            <SimpleForm>
                <MembershipInstitutionFormFields />
            </SimpleForm>
        </Edit>
    </Box>
);