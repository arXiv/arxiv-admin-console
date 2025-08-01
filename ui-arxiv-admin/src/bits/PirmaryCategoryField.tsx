
import React from 'react';
import {useRecordContext, FieldProps, RecordContextProvider} from 'react-admin';

import {components as adminComponents} from "../types/admin-api";
import CategoryField from "./CategoryField";
type SubmissionCategoryModel = adminComponents['schemas']['SubmissionCategoryModel'];

const PrimaryCategoryField: React.FC<FieldProps> = (props) => {
    const record = useRecordContext();
    const { source } = props;
    if (!record || !source) return null;
    const categories: SubmissionCategoryModel[] = record[source];
    if (!categories) return null;
    if (categories.length === 0) return null;
    const primary = categories.filter((cat) => cat.is_primary);
    if (primary.length === 0) return null;
    const category = primary[0].category;
    const cat = category.split(".");
    const catRecord = {archive: cat[0], subject_class: cat[1], category: category};
    return (
        <RecordContextProvider value={catRecord}>
            <CategoryField sourceCategory={"archive"} sourceClass={"subject_class"} source={"category"}  />
        </RecordContextProvider>
    );
};

export default PrimaryCategoryField;
