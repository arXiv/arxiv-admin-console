import React from "react";
import Typography from "@mui/material/Typography";
// import Link from "@mui/material/Link";

export const PrepReportNum = (
    <Typography variant={"body1"}>Required only when supplied by author's institution
        <li>Enter your institution's locally assigned publication number.</li>
        <li>Do not put any other information in this field.</li>
        <li>Example: <code>Report-no: EFI-94-11</code></li></Typography>
);

export const  PrepJoyrnalRef = (
    <Typography variant={"body1"}>
        <li>This field is only for a full bibliographic reference if the article has already appeared in a journal or a proceedings.</li>
        <li>Indicate the volume number, year, and page number (or page range).</li>
        <li>If your submission has not appeared yet, but you would still like to indicate where it will be published, use the Comments: field. Please note that the Comments field can only be updated by submitting a replacement.</li>
        <li>If there are multiple full bibliographic references associated with the paper, for example the original and an erratum, then separate them with a semicolon and a space, e.g.
            <code>J.Hasty Results 1 (2008) 1-9; Erratum: J.Hasty Results 2 (2008) 1-2</code></li>
        <li>In most cases, submissions are not yet published, and so Journal-ref information is not available. A facility is provided for you to add a journal reference to your previously submitted article at a later date.</li>
        <li>Do not put URLs into this field, as they will not be converted into links.</li>
    </Typography>);

export const PrepDOI = (
    <Typography>
        <li>This field is only for a DOI (Digital Object Identifier) that resolves (links) to another version of the article, such as a journal article. Do not add the arXiv assigned DOI to this field.
            </li>

            <li>If there are multiple DOIs associated with an article, separate them with a space.</li>

            <li>Do not include any other information in this field. In most cases, submissions are not yet published, and so DOI information will be added by the author at a later date. A facility is provided for adding a Journal-ref and DOI to an already public arXiv-ID.</li>

            <li>Articles submitted to arXiv are automatically assigned DOIs that correspond to their arXiv ID, and the associated article metadata is submitted to DataCite at no cost to the authors. Read more about understanding arXiv assigned DOIs.</li>

            <li>DOIs have the form <code>10.48550/arXiv.2202.01037</code></li>
    </Typography>);

export const PrepMSCClass = (
    <Typography>
        <li>
            For submissions to the math archive, this field is used to indicate the mathematical classification code according to the Mathematics Subject Classification. Here is an example</li>
            <pre>
                <code>
                MSC-class: 14J60 (Primary) 14F05, 14J26 (Secondary)
                </code>
            </pre>
            Put the "Primary" and "Secondary" keywords in parentheses. If there is only a Primary classification, the "Primary" keyword is optional. Separate multiple classification keys with commas.
    </Typography>
)


export const PrepACMClass = (
    <Typography>
    <li>For submissions to the cs archive, this field is used to indicate the classification code according to the ACM Computing Classification System (or see this overview). Here is an example</li>
        <pre>
                <code>
        ACM-class: F.2.2; I.2.7
                </code>
            </pre>
(Separate multiple classifications by a semicolon and a space.)
    </Typography>
)

