import { Link } from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import {RuntimeContext} from "../RuntimeContext";
import {useContext} from "react";
import UriTemplate from 'uri-templates';
import {useRecordContext} from "react-admin";


const ArxivCheckSubmissionLink = () => {
    const record = useRecordContext();
    const runtimeProps = useContext(RuntimeContext);

    if (!record) return null;

    const url = UriTemplate(runtimeProps.URLS.CheckSubmissionLink).fill({
        arxivCheck: runtimeProps.ARXIV_CHECK,
        submissionId: record.id,
    });

    console.log(url);
    return (
        <a href={url} target="_blank" rel="noopener noreferrer">
            <CheckIcon />
        </a>
    );
};

export default ArxivCheckSubmissionLink;
