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
import PaperOwnersList from "../bits/PaperOwnersList";
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
                                <Tooltip title={<Typography variant={"body1"}>Required only when supplied by author's institution
                                    <li>Enter your institution's locally assigned publication number.</li>
                                    <li>Do not put any other information in this field.</li>
                                    <li>Example: Report-no: EFI-94-11</li></Typography>} >
                                    <Typography>Report Number</Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="report_num" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>MSC Class</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="msc_class" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>ACM Class</FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="acm_class" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>
                                <Tooltip title={<Typography variant={"body1"}>
                                    <li>This field is only for a full bibliographic reference if the article has already appeared in a journal or a proceedings.</li>
                                    <li>Indicate the volume number, year, and page number (or page range).</li>
                                    <li>If your submission has not appeared yet, but you would still like to indicate where it will be published, use the Comments: field. Please note that the Comments field can only be updated by submitting a replacement.</li>
                                    <li>If there are multiple full bibliographic references associated with the paper, for example the original and an erratum, then separate them with a semicolon and a space, e.g.
                                        <code>J.Hasty Results 1 (2008) 1-9; Erratum: J.Hasty Results 2 (2008) 1-2</code></li>
                                    <li>In most cases, submissions are not yet published, and so Journal-ref information is not available. A facility is provided for you to add a journal reference to your previously submitted article at a later date.</li>
                                    <li>Do not put URLs into this field, as they will not be converted into links.</li>
                                </Typography>} >
                                    <Typography>JournalRef</Typography>
                                </Tooltip>
                            </FieldNameCell>
                            <TableCell>
                                <PlainTextInput source="journal_ref" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>DOI</FieldNameCell>
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


