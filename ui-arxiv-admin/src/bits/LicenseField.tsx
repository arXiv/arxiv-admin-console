import React, {useEffect} from "react";
import {FieldProps, useDataProvider, useNotify, useRecordContext} from "react-admin";
import { paths as adminApi } from "../types/admin-api";

type LicensesType = adminApi["/v1/licenses/"]["get"]["responses"]["200"]["content"]["application/json"];
type LicenseType = LicensesType[0];

const LicenseField: React.FC<FieldProps> = ({source}) => {
    const record = useRecordContext();
    const [licenseOptions, setLicenseOptions] = React.useState<LicensesType>([]);
    const dataProvider = useDataProvider();
    const notify = useNotify();

    useEffect(() => {
        async function getLicenses() {
            try {
                const response = await dataProvider.getList("licenses",
                    {
                        sort: { field: 'sequence', order: 'ASC' },
                    });
                setLicenseOptions(response.data);
            }
            catch (error) {
                // @ts-ignore
                notify(error.message, "warning");
            }
        }
        getLicenses();
    }, []);

    const value = record?.[source];
    const selectedOption = value && licenseOptions.length > 0 ? licenseOptions.find(license => license.id === value) || null : null;

    return (
        <span>{selectedOption ? selectedOption.label : value || "No license"}</span>
    );
};

export default LicenseField;