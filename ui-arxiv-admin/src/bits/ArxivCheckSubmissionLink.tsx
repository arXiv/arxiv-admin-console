import React from 'react';
import CheckIcon from '@mui/icons-material/Check';
import {RuntimeContext} from "../RuntimeContext";
import {useContext} from "react";
import UriTemplate from 'uri-templates';
import {FieldProps, useRecordContext, TextField} from "react-admin";

const ArxivCheckSubmissionLink: React.FC<FieldProps> = (props) => {
    const record = useRecordContext();
    const runtimeProps = useContext(RuntimeContext);

    if (!record) return null;
    if (!runtimeProps.ARXIV_CHECK) return null;

    const {source} = props;

    const url = UriTemplate(runtimeProps.URLS.CheckSubmissionLink).fill({
        arxivCheck: runtimeProps.ARXIV_CHECK,
        submissionId: record.id,
    });

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
        e.preventDefault();
        // Use a named window instead of "_blank" to reuse the tab
        const windowName = "arxiv-check";
        window.open(url, windowName, "noopener,noreferrer");
    };

    const display = source ? (<TextField {...props} />) : <CheckIcon sx={{width: 16, height: 16}}/>;

    return (
        <a href={url} onClick={handleClick}>
            {display}
        </a>
    );
};

export default ArxivCheckSubmissionLink;
