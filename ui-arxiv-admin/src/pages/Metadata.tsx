import {
    Card,
    CardContent,
    Paper,
    Grid,
    ToggleButton,
    Typography,
    useMediaQuery,
    Switch,
    FormControlLabel, IconButton
} from '@mui/material';
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
    SimpleShowLayout,
    Show,
    DateInput, useListContext, SelectInput, useShowContext, Identifier, useDataProvider
} from 'react-admin';

import LinkIcon from '@mui/icons-material/Link';
import MetadataIcon from '@mui/icons-material/Edit';


import {addDays} from 'date-fns';

import React, {ReactNode, useEffect, useState} from "react";
import CircularProgress from "@mui/material/CircularProgress";
import CategoryField from "../bits/CategoryField";
import SubmissionCategoriesField from "../bits/SubmissionCategoriesField";
import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableRow from "@mui/material/TableRow";
import TableCell, {TableCellProps} from "@mui/material/TableCell";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import PaperOwnersList from "../components/PaperOwnersList";
import SubmissionHistoryList from "../bits/SubmissionHistoryList";
import AdminLogList from "../bits/AdminLogList";
import PaperAdminAddOwnerDialog from "../components/PaperAdminAddOwnerDialog";
import {useNavigate} from "react-router-dom";
import {paths as adminApi} from '../types/admin-api';
import FieldNameCell from "../bits/FieldNameCell";
import PlainTextInput from '../bits/PlainTextInput';
import CategoryInput from "../bits/CategoryInput";
import Tooltip from "@mui/material/Tooltip";
import SourceFlagsInput from '../bits/SourceFlagsInput';
import SourceFormatInput from "../bits/SourceFormatInput";
import LicenseInput from "../bits/LicenseInput";
import {PrepACMClass, PrepDOI, PrepJoyrnalRef, PrepMSCClass, PrepReportNum} from "../helptexts/Prep";

type MetadataT = adminApi['/v1/metadata/document_id/{document_id}']['get']['responses']['200']['content']['application/json'];


const MetadataEditContents = () => {
    const record = useRecordContext();
    const [openAddOwnerDialog, setOpenAddOwnerDialog] = React.useState(false);
    const navigate = useNavigate();
    const [metadata, setMetadata] = useState<MetadataT | null>(null);
    const dataProvider =  useDataProvider();

    return (
        <SimpleForm>
            <Box gap={1} display="flex" flexDirection="column"
                 sx={{
                     width: '100%',
                     '& .MuiBox-root': {  // Targets all Box components inside
                         width: '100%'
                     },
                     '& .MuiTable-root': {  // Targets all Table components inside
                         width: '100%'
                     }
                 }}
            >

                {/* Paper Details */}
                <Paper elevation={3} style={{padding: '1em'}}>
                    <Table size="small">
                        <TableRow>
                            <FieldNameCell>ID</FieldNameCell>
                            <TableCell>
                                <TextField source={"id"} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Paper ID</FieldNameCell>
                            <TableCell>
                                <TextField source={"paper_id"} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Title</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="title" fontSize={"1.2rem"} />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <FieldNameCell>Authors</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="authors"  />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <FieldNameCell>License</FieldNameCell>
                            <TableCell>
                                <LicenseInput source="license" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Comments</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="comments" multiline={true} rows={2} resizable={"vertical"} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Abstract</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="abstract" multiline={true} rows={8} resizable={"vertical"} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Proxy</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="proxy" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Source Format</FieldNameCell>
                            <TableCell>
                                <SourceFormatInput source="source_format" name={""} />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Source Flags</FieldNameCell>
                            <TableCell>
                                <SourceFlagsInput source="source_flags" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Is Withdrawn</FieldNameCell>
                            <TableCell>
                                <BooleanInput label={""} source={"is_withdrawn"} helperText={false}  />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepReportNum} >
                                    <Typography>Report Number</Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="report_num" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepMSCClass}>
                                    <Typography>
                                        MSC Class
                                    </Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="msc_class" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepACMClass}>
                                    <Typography>
                                        ACM Class
                                    </Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="acm_class" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepJoyrnalRef} >
                                    <Typography>JournalRef</Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="journal_ref" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={PrepDOI} >
                                    <Typography>DOI</Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="doi" />
                            </TableCell>
                        </TableRow>

                    </Table>
                </Paper>
            </Box>
        </SimpleForm>
    );
};

export const MetadataEdit = () => (
    <Edit>
        <MetadataEditContents/>
    </Edit>
);


