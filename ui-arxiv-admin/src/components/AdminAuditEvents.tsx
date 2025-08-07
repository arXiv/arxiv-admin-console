/**
 * Tapir Admin audit event interface
 *
 * Each admin event is represented by a sub-class of AdminAuditEvent.
 */

import { UserVetoStatus, UserFlags } from '../helptexts/userStatus';

import {paths as adminApi} from '../types/admin-api';
import React from "react";
import Typography from "@mui/material/Typography";
import {RaRecord, ReferenceField, TextField, Identifier} from "react-admin";
import UserNameField from "../bits/UserNameField";
import {Box} from "@mui/material";
type TapirAdminAudit = adminApi['/v1/tapir_admin_audit/{id}']['get']['responses']['200']['content']['application/json'];

export enum AdminAuditActionEnum {
    ADD_COMMENT = "add-comment",
    ADD_PAPER_OWNER = "add-paper-owner",
    ADD_PAPER_OWNER_2 = "add-paper-owner-2",
    ARXIV_CHANGE_PAPER_PW = "arXiv-change-paper-pw",
    ARXIV_CHANGE_STATUS = "arXiv-change-status",
    ARXIV_MAKE_AUTHOR = "arXiv-make-author",
    ARXIV_MAKE_NONAUTHOR = "arXiv-make-nonauthor",
    ARXIV_REVOKE_PAPER_OWNER = "arXiv-revoke-paper-owner",
    ARXIV_UNREVOKE_PAPER_OWNER = "arXiv-unrevoke-paper-owner",
    BECOME_USER = "become-user",
    CHANGE_EMAIL = "change-email",
    CHANGE_PAPER_PW = "change-paper-pw",
    CHANGE_PASSWORD = "change-password",
    ENDORSED_BY_SUSPECT = "endorsed-by-suspect",
    FLIP_FLAG = "flip-flag",
    GOT_NEGATIVE_ENDORSEMENT = "got-negative-endorsement",
    MAKE_MODERATOR = "make-moderator",
    REVOKE_PAPER_OWNER = "revoke-paper-owner",
    SUSPEND_USER = "suspend-user",
    UNMAKE_MODERATOR = "unmake-moderator",
    UNSUSPEND_USER = "unsuspend-user",
}


const normalizeBoolean = (value: string | number | boolean): boolean => {
    if (typeof value === 'string') {
        return ['yes', 'true', '1'].includes(value.toLowerCase());
    } else if (typeof value === 'number') {
        return value !== 0;
    } else {
        return value;
    }
};



export abstract class AdminAuditEvent {
    /**
     * Base class for all administrative audit events.
     * 
     * This abstract base class defines the common structure and interface
     * for all audit events in the system. Each audit event captures information
     * about an administrative action including who performed it, who was affected,
     * when it occurred, and relevant session/network information.
     */
    
    timestamp: number;
    admin_user: string;
    affected_user: string;
    session_id?: string | null;
    remote_ip?: string | null;
    remote_hostname?: string | null;
    tracking_cookie?: string | null;
    protected _comment?: string | null;
    protected _data?: string | null;
    
    static readonly _action: AdminAuditActionEnum;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            data?: string | null;
            timestamp?: number | null;
        } = {}
    ) {
        this.admin_user = admin_id;
        this.affected_user = affected_user;
        this.session_id = session_id;
        this.timestamp = options.timestamp ?? Math.floor(Date.now() / 1000);
        this.remote_ip = options.remote_ip;
        this.remote_hostname = options.remote_hostname;
        this.tracking_cookie = options.tracking_cookie;
        this._comment = options.comment;
        this._data = options.data;
    }

    get comment(): string {
        return this._comment || '';
    }

    get data(): string {
        return this._data || '';
    }


    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        /**
         * Generate constructor parameters from an audit record.
         *
         * This method can be overridden by subclasses to provide custom
         * parameter generation for their constructors.
         */
        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            data: audit_record.data,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000, // Convert ISO date to Unix timestamp
        };
    }

    describe(): React.ReactElement {
        return <Typography>{this.data}</Typography>;
    }
}


export class AdminAudit_AddComment extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.ADD_COMMENT;

    describe(): React.ReactElement {

        return (
            <Box >
                <ReferenceField reference={"users"} source={"admin_user"} >
                    <UserNameField />
                </ReferenceField>
                {" commented on "}
                <ReferenceField reference={"users"} source={"affected_user"} >
                    <UserNameField />
                </ReferenceField>
                {": "}
                <TextField source={"comment"} />
            </Box>
        );
    }
}


export abstract class AdminAudit_PaperEvent extends AdminAuditEvent {
    /**
     * Base class for audit events related to paper ownership and management.
     *
     * This class handles audit events that involve paper-related actions,
     * storing the paper ID as the data field and validating it as an integer.
     */

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            paper_id: string;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { paper_id, ...restOptions } = options;
        super(admin_id, affected_user, session_id, {
            ...restOptions,
            data: paper_id,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            paper_id: audit_record.data,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }
}


export class AdminAudit_AddPaperOwner extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.ADD_PAPER_OWNER;

    describe(): React.ReactElement {

        return (
            <Box component={"span"} >
                <ReferenceField reference={"users"} source={"admin_user"} >
                    <UserNameField />
                </ReferenceField>
                {" made "}
                <ReferenceField reference={"users"} source={"affected_user"} >
                    <UserNameField />
                </ReferenceField>

                {" an owner of paper "}
                <ReferenceField reference={"documents"} source={"data"} >
                    <TextField source={"paper_id"} />
                </ReferenceField>
            </Box>
        );
    }
}

export class AdminAudit_AddPaperOwner2 extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.ADD_PAPER_OWNER_2;

    describe(): React.ReactElement {
        return (
            <Box component={"span"} >
                <ReferenceField reference={"users"} source={"admin_user"} >
                    <UserNameField />
                </ReferenceField>
                {" made "}
                <ReferenceField reference={"users"} source={"affected_user"} >
                    <UserNameField />
                </ReferenceField>

                {" an owner of paper "}
                <ReferenceField reference={"documents"} source={"data"} >
                    <TextField source={"paper_id"} />
                </ReferenceField>
                {" through the process-ownership screen"}
            </Box>
        );
    }
}

export class AdminAudit_ChangePaperPassword extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.CHANGE_PAPER_PW;

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" changed the paper password for "}
                <ReferenceField reference="documents" source="data">
                    <TextField source="paper_id" />
                </ReferenceField>
                {" which was submitted by "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
            </Box>
        );
    }
}

export class AdminAudit_AdminChangePaperPassword extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.ARXIV_CHANGE_PAPER_PW;

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" changed the paper password for "}
                <ReferenceField reference="documents" source="data">
                    <TextField source="paper_id" />
                </ReferenceField>
                {" which was submitted by "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export class AdminAudit_AdminMakeAuthor extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.ARXIV_MAKE_AUTHOR;

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" made "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" an author of "}
                <ReferenceField reference="documents" source="data">
                    <TextField source="paper_id" />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export class AdminAudit_AdminMakeNonauthor extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.ARXIV_MAKE_NONAUTHOR;

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" made "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" a nonauthor of "}
                <ReferenceField reference="documents" source="data">
                    <TextField source="paper_id" />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export class AdminAudit_AdminRevokePaperOwner extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.ARXIV_REVOKE_PAPER_OWNER;

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" revoked "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" the ownership of "}
                <ReferenceField reference="documents" source="data">
                    <TextField source="paper_id" />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export class AdminAudit_AdminUnrevokePaperOwner extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.ARXIV_UNREVOKE_PAPER_OWNER;

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" restored "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" the ownership of "}
                <ReferenceField reference="documents" source="data">
                    <TextField source="paper_id" />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export class AdminAudit_RevokePaperOwner extends AdminAudit_PaperEvent {
    static readonly _action = AdminAuditActionEnum.REVOKE_PAPER_OWNER;

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" revoked "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" the ownership of "}
                <ReferenceField reference="documents" source="data">
                    <TextField source="paper_id" />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}


export class AdminAudit_BecomeUser extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.BECOME_USER;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            new_session_id: string;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { new_session_id, ...restOptions } = options;
        const data = new_session_id.toString();
        parseInt(data); // Validate it's a number
        super(admin_id, affected_user, session_id, {
            ...restOptions,
            data,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            new_session_id: audit_record.data,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" impersonated "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
            </Box>
        );
    }
}

export class AdminAudit_ChangeEmail extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.CHANGE_EMAIL;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            email: string;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { email, ...restOptions } = options;
        super(admin_id, affected_user, session_id, {
            ...restOptions,
            data: email,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            email: audit_record.data,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" changed email of "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" to "}
                <TextField source="data" />
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export class AdminAudit_ChangePassword extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.CHANGE_PASSWORD;

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" changed password of "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export abstract class AdminAudit_EndorseEvent extends AdminAuditEvent {
    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            endorser: string;
            endorsee: string;
            category: string;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { endorser, endorsee, category, ...restOptions } = options;
        parseInt(endorser); // Validate it's a number
        parseInt(endorsee); // Validate it's a number
        const data = `${endorser} ${category} ${endorsee}`;
        super(admin_id, affected_user, session_id, {
            ...restOptions,
            data,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        const data = audit_record.data.split(" ");
        if (data.length !== 3) {
            console.error(`data '${audit_record.data}' is not valid. ` + JSON.stringify(data));
            throw new Error(`data format '${audit_record.data}' is not valid`);
        }
        const [endorser, category, endorsee] = data;

        if (!/^\d+$/.test(endorser) || 
            !/^\d+$/.test(endorsee) || 
            !/[\w\-._\d]+/.test(category)) {
            console.error(`data '${audit_record.data}' is not valid. ` + JSON.stringify(data));
            throw new Error(`validation '${audit_record.data}' failed`);
        }

        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            endorser,
            endorsee,
            category,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }

    describe(): React.ReactElement {
        const data = this.data.split(" ");
        if (data.length === 3) {
            const [endorser, category, endorsee] = data;
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="endorser" record={{endorser}}>
                        <UserNameField />
                    </ReferenceField>
                    {" ? "}
                    <ReferenceField reference="users" source="endorsee" record={{endorsee}}>
                        <UserNameField />
                    </ReferenceField>
                    {` for ${category}`}
                </Box>
            );
        }
        return <Typography>{JSON.stringify(data)}</Typography>;
    }
}

export class AdminAudit_EndorsedBySuspect extends AdminAudit_EndorseEvent {
    static readonly _action = AdminAuditActionEnum.ENDORSED_BY_SUSPECT;

    describe(): React.ReactElement {
        const data = this.data.split(" ");
        if (data.length === 3) {
            const [endorser, category, endorsee] = data;
            return (
                <Box component="span">
                    {"A flagged user "}
                    <ReferenceField reference="users" source="endorser" record={{endorser}}>
                        <UserNameField />
                    </ReferenceField>
                    {" endorsed "}
                    <ReferenceField reference="users" source="endorsee" record={{endorsee}}>
                        <UserNameField />
                    </ReferenceField>
                    {` for ${category}`}
                </Box>
            );
        }
        return <Typography>{JSON.stringify(data)}</Typography>;
    }
}

export class AdminAudit_GotNegativeEndorsement extends AdminAudit_EndorseEvent {
    static readonly _action = AdminAuditActionEnum.GOT_NEGATIVE_ENDORSEMENT;

    describe(): React.ReactElement {
        const data = this.data.split(" ");
        if (data.length === 3) {
            const [endorser, category, endorsee] = data;
            return (
                <Box component="span">
                    {"A flagged user "}
                    <ReferenceField reference="users" source="endorser" record={{endorser}}>
                        <UserNameField />
                    </ReferenceField>
                    {" rejected an endorsement request by "}
                    <ReferenceField reference="users" source="endorsee" record={{endorsee}}>
                        <UserNameField />
                    </ReferenceField>
                    {` for ${category}`}
                </Box>
            );
        }
        return <Typography>{JSON.stringify(data)}</Typography>;
    }
}

export class AdminAudit_MakeModerator extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.MAKE_MODERATOR;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            category: string;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { category, ...restOptions } = options;
        super(admin_id, affected_user, session_id, {
            ...restOptions,
            data: category,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            category: audit_record.data,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" made "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" a moderator of "}
                <TextField source="data" />
            </Box>
        );
    }
}

export class AdminAudit_UnmakeModerator extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.UNMAKE_MODERATOR;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            category: string;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { category, ...restOptions } = options;
        super(admin_id, affected_user, session_id, {
            ...restOptions,
            data: category,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            category: audit_record.data,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" removed "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" from moderator of "}
                <TextField source="data" />
            </Box>
        );
    }
}

export class AdminAudit_SuspendUser extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.SUSPEND_USER;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        } = {}
    ) {
        super(admin_id, affected_user, session_id, {
            ...options,
            data: `${UserFlags.TAPIR_FLAG_BANNED}=1`,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" suspended/banned the account of "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export class AdminAudit_UnsuspendUser extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.UNSUSPEND_USER;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        } = {}
    ) {
        super(admin_id, affected_user, session_id, {
            ...options,
            data: `${UserFlags.TAPIR_FLAG_BANNED}=0`,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }

    describe(): React.ReactElement {
        return (
            <Box component="span">
                <ReferenceField reference="users" source="admin_user">
                    <UserNameField />
                </ReferenceField>
                {" unsuspended the account of "}
                <ReferenceField reference="users" source="affected_user">
                    <UserNameField />
                </ReferenceField>
                {" "}
                <TextField source="comment" />
            </Box>
        );
    }
}

export class AdminAudit_ChangeStatus extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.ARXIV_CHANGE_STATUS;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            status_before: UserVetoStatus;
            status_after: UserVetoStatus;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { status_before, status_after, ...restOptions } = options;
        if (typeof status_before !== 'string' || !Object.values(UserVetoStatus).includes(status_before)) {
            throw new Error(`status_before '${status_before}' is not a UserStatus`);
        }
        if (typeof status_after !== 'string' || !Object.values(UserVetoStatus).includes(status_after)) {
            throw new Error(`status_after '${status_after}' is not a UserStatus`);
        }
        super(admin_id, affected_user, session_id, {
            ...restOptions,
            data: `${status_before} -> ${status_after}`,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        const match = audit_record.data.match(/^([\w\-]*) -> ([\w\-]+)$/);
        if (!match) {
            throw new Error(`Invalid status change format: ${audit_record.data}`);
        }

        const status_before = match[1] as UserVetoStatus;
        const status_after = match[2] as UserVetoStatus;

        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
            status_before,
            status_after,
        };
    }

    describe(): React.ReactElement {
        try {
            const elements = this.data.split('->');
            if (elements.length === 2) {
                const status_before = elements[0].trim();
                const status_after = elements[1].trim();
                return (
                    <Box component="span">
                        <ReferenceField reference="users" source="admin_user">
                            <UserNameField />
                        </ReferenceField>
                        {` changed the veto status of `}
                        <ReferenceField reference="users" source="affected_user">
                            <UserNameField />
                        </ReferenceField>
                        {status_before ? (
                            <>
                                {" from "}
                                <Typography component="span" fontWeight="bold" color="secondary">
                                    {status_before}
                                </Typography>
                            </>
                        ) : null}
                        {" to "}
                        <Typography component="span" fontWeight="bold" color="secondary">
                            {status_after}
                        </Typography>

                        <Typography component="span" >
                            {" "}
                            {this.comment}
                        </Typography>
                    </Box>
                );
            }
        }
        catch (e) {
            console.error(e);
        }
        return <Typography>{this.data}</Typography>;
    }
}

export abstract class AdminAudit_SetFlag extends AdminAuditEvent {
    static readonly _action = AdminAuditActionEnum.FLIP_FLAG;
    static readonly _flag: UserFlags;
    static readonly _value_name: string;
    static readonly _value_type: 'boolean' | 'number' | 'string';

    protected constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        data: string,
        options: {
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        } = {}
    ) {
        super(admin_id, affected_user, session_id, {
            ...options,
            data,
        });
    }

    static getInitParams(audit_record: TapirAdminAudit): Record<string, any> {
        const data = audit_record.data.split('=');
        if (data.length !== 2) {
            throw new Error(`data '${audit_record.data}' is not a valid flag=value`);
        }
        const flag = data[0] as UserFlags;
        const value = data[1];

        return {
            admin_user: audit_record.admin_user?.toString() || '',
            affected_user: audit_record.affected_user.toString(),
            session_id: audit_record.session_id?.toString() || '',
            comment: audit_record.comment,
            flag,
            value,
            remote_ip: audit_record.ip_addr,
            remote_hostname: audit_record.remote_host,
            tracking_cookie: audit_record.tracking_cookie,
            timestamp: new Date(audit_record.log_date).getTime() / 1000,
        };
    }

    describe(): React.ReactElement {
        const constructor = this.constructor as typeof AdminAudit_SetFlag;
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            let value: string;
            if (constructor._value_type === 'boolean') {
                value = parseInt(value1) ? 'true' : 'false';
            } else {
                value = this.data;
            }
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {` set the ${constructor._flag} of `}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                    {` to ${value}`}
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetGroupTest extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.ARXIV_FLAG_GROUP_TEST;
    static readonly _value_name = 'group_test';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            group_test: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { group_test, ...restOptions } = options;
        const normalized = normalizeBoolean(group_test);
        const data = `${AdminAudit_SetGroupTest._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            let value = parseInt(value1) ? 'true' : 'false';
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {` set the test group flag of `}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                    {` to ${value}`}
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }

}

export class AdminAudit_SetProxy extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.ARXIV_FLAG_PROXY;
    static readonly _value_name = 'proxy';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            proxy: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { proxy, ...restOptions } = options;
        const normalized = normalizeBoolean(proxy);
        const data = `${AdminAudit_SetProxy._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            let value = parseInt(value1) ? 'true' : 'false';
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {` set the proxy of `}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                    {` to ${value}`}
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetSuspect extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.ARXIV_FLAG_SUSPECT;
    static readonly _value_name = 'suspect';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            suspect: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { suspect, ...restOptions } = options;
        const normalized = normalizeBoolean(suspect);
        const data = `${AdminAudit_SetSuspect._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {parseInt(value1) ? " flagged " : " unflagged "}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                    {" "}
                    <TextField source="comment" />
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }

}

export class AdminAudit_SetXml extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.ARXIV_FLAG_XML;
    static readonly _value_name = 'xml';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            xml: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { xml, ...restOptions } = options;
        const normalized = normalizeBoolean(xml);
        const data = `${AdminAudit_SetXml._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {" set xml flag of "}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                    {parseInt(value1) ? " to true" : " to false"}
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetEndorsementValid extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.ARXIV_ENDORSEMENT_FLAG_VALID;
    static readonly _value_name = 'endorsement_valid';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            endorsement_valid: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { endorsement_valid, ...restOptions } = options;
        const normalized = normalizeBoolean(endorsement_valid);
        const data = `${AdminAudit_SetEndorsementValid._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {parseInt(value1) ? " made the endorsement valid for " : " made the endorsement invalid for "}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                    {" "}
                    <TextField source="comment" />
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}


export class AdminAudit_SetPointValue extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.ARXIV_ENDORSEMENT_POINT_VALUE;
    static readonly _value_name = 'point_value';
    static readonly _value_type = 'number' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            point_value: number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { point_value, ...restOptions } = options;
        const data = `${AdminAudit_SetPointValue._flag}=${point_value}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {" set the point value of "}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                    {` to ${value1}`}
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetEndorsementRequestsValid extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.ARXIV_ENDORSEMENT_REQUEST_FLAG_VALID;
    static readonly _value_name = 'endorsement_requests_valid';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            endorsement_requests_valid: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { endorsement_requests_valid, ...restOptions } = options;
        const normalized = normalizeBoolean(endorsement_requests_valid);
        const data = `${AdminAudit_SetEndorsementRequestsValid._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField/>
                    </ReferenceField>
                    {parseInt(value1) ? " set endorsement request of " : " cleared entorsement request of "}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField/>
                    </ReferenceField>
                    {" Comment: "}
                    <TextField source="comment" />
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetEmailBouncing extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.TAPIR_EMAIL_BOUNCING;
    static readonly _value_name = 'email_bouncing';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            email_bouncing: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { email_bouncing, ...restOptions } = options;
        const normalized = normalizeBoolean(email_bouncing);
        const data = `${AdminAudit_SetEmailBouncing._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField/>
                    </ReferenceField>
                    {parseInt(value1) ? " set email bouncing of " : " cleared email bouncing of "}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField/>
                    </ReferenceField>
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetBanned extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.TAPIR_FLAG_BANNED;
    static readonly _value_name = 'banned';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            banned: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { banned, ...restOptions } = options;
        const normalized = normalizeBoolean(banned);
        const data = `${AdminAudit_SetBanned._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {  parseInt(value1) ? " banned " : " unbanned " }
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                    {" "}
                    <TextField source="comment" />
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetEditSystem extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.TAPIR_FLAG_EDIT_SYSTEM;
    static readonly _value_name = 'edit_system';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            edit_system: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { edit_system, ...restOptions } = options;
        const normalized = normalizeBoolean(edit_system);
        const data = `${AdminAudit_SetEditSystem._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            if (parseInt(value1)) {
                return (
                    <Box component="span">
                        <ReferenceField reference="users" source="admin_user">
                            <UserNameField />
                        </ReferenceField>
                        {" made "}
                        <ReferenceField reference="users" source="affected_user">
                            <UserNameField />
                        </ReferenceField>
                        {" a sysadmin."}
                        <TextField source="comment" />
                    </Box>
                );
            } else {
                return (
                    <Box component="span">
                        <ReferenceField reference="users" source="admin_user">
                            <UserNameField />
                        </ReferenceField>
                        {" cleared sysadmin of "}
                        <ReferenceField reference="users" source="affected_user">
                            <UserNameField />
                        </ReferenceField>
                        {" "}
                        <TextField source="comment" />
                    </Box>
                );
            }
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetEditUsers extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.TAPIR_FLAG_EDIT_USERS;
    static readonly _value_name = 'edit_users';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            edit_users: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { edit_users, ...restOptions } = options;
        const normalized = normalizeBoolean(edit_users);
        const data = `${AdminAudit_SetEditUsers._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            if (parseInt(value1)) {
                return (
                    <Box component={"span"}>
                        <ReferenceField reference={"users"} source={"admin_user"} >
                            <UserNameField />
                        </ReferenceField>
                        {" made "}
                        <ReferenceField reference={"users"} source={"affected_user"} >
                            <UserNameField />
                        </ReferenceField>
                        {" an administrator. "}
                        <TextField source="comment" />
                    </Box>
                );
            } else {
                return (
                    <Box component={"span"}>
                        <ReferenceField reference={"users"} source={"admin_user"} >
                            <UserNameField />
                        </ReferenceField>
                        {" cleared admin of "}
                        <ReferenceField reference={"users"} source={"affected_user"} >
                            <UserNameField />
                        </ReferenceField>
                        {" "}
                        <TextField source="comment" />
                    </Box>
                );
            }
        }
        return <Typography>{this.data}</Typography>;
    }
}

export class AdminAudit_SetEmailVerified extends AdminAudit_SetFlag {
    static readonly _flag = UserFlags.TAPIR_FLAG_EMAIL_VERIFIED;
    static readonly _value_name = 'verified';
    static readonly _value_type = 'boolean' as const;

    constructor(
        admin_id: string,
        affected_user: string,
        session_id: string,
        options: {
            verified: boolean | string | number;
            remote_ip?: string | null;
            remote_hostname?: string | null;
            tracking_cookie?: string | null;
            comment?: string | null;
            timestamp?: number | null;
        }
    ) {
        const { verified, ...restOptions } = options;
        const normalized = normalizeBoolean(verified);
        const data = `${AdminAudit_SetEmailVerified._flag}=${normalized ? 1 : 0}`;
        super(admin_id, affected_user, session_id, data, restOptions);
    }

    describe(): React.ReactElement {
        const elements = this.data.split('=');
        if (elements.length === 2) {
            const value1 = elements[1];
            return (
                <Box component="span">
                    <ReferenceField reference="users" source="admin_user">
                        <UserNameField />
                    </ReferenceField>
                    {parseInt(value1) ? " verified the email of " : " unverified the email of "}
                    <ReferenceField reference="users" source="affected_user">
                        <UserNameField />
                    </ReferenceField>
                </Box>
            );
        }
        return <Typography>{this.data}</Typography>;
    }
}


const setFlagEventClasses: Record<string, any> = {
    [UserFlags.ARXIV_FLAG_GROUP_TEST]: AdminAudit_SetGroupTest,
    [UserFlags.ARXIV_FLAG_PROXY]: AdminAudit_SetProxy,
    [UserFlags.ARXIV_FLAG_SUSPECT]: AdminAudit_SetSuspect,
    [UserFlags.ARXIV_FLAG_XML]: AdminAudit_SetXml,
    [UserFlags.ARXIV_ENDORSEMENT_FLAG_VALID]: AdminAudit_SetEndorsementValid,
    [UserFlags.ARXIV_ENDORSEMENT_POINT_VALUE]: AdminAudit_SetPointValue,
    [UserFlags.ARXIV_ENDORSEMENT_REQUEST_FLAG_VALID]: AdminAudit_SetEndorsementRequestsValid,
    [UserFlags.TAPIR_EMAIL_BOUNCING]: AdminAudit_SetEmailBouncing,
    [UserFlags.TAPIR_FLAG_BANNED]: AdminAudit_SetBanned,
    [UserFlags.TAPIR_FLAG_EDIT_SYSTEM]: AdminAudit_SetEditSystem,
    [UserFlags.TAPIR_FLAG_EDIT_USERS]: AdminAudit_SetEditUsers,
    [UserFlags.TAPIR_FLAG_EMAIL_VERIFIED]: AdminAudit_SetEmailVerified,
};

function adminAuditFlipFlagInstantiator(audit_record: TapirAdminAudit): AdminAuditEvent {
    const params = AdminAudit_SetFlag.getInitParams(audit_record);
    const flag = params.flag as UserFlags;
    const value = params.value;
    const eventClass = setFlagEventClasses[flag];
    
    if (!eventClass) {
        throw new Error(`${audit_record.action}.${flag} is not a valid admin action of flip flag`);
    }
    
    if (!eventClass._value_name) {
        throw new Error('AdminAudit_SetFlag is a base class and not intended to be instantiated directly');
    }
    
    const valueName = eventClass._value_name;
    
    // Create options object with the specific flag name and exclude generic properties
    const { flag: _, value: __, admin_user, affected_user, session_id, ...restOptions } = params as any;
    const options = {
        ...restOptions,
        [valueName]: value,
    };
    
    return new eventClass(admin_user, affected_user, session_id, options);
}

type EventClass = typeof AdminAuditEvent;
type EventFactory = (audit_record: TapirAdminAudit) => AdminAuditEvent;

const eventClasses: Record<string, EventClass | EventFactory> = {
    [AdminAuditActionEnum.ADD_COMMENT]: AdminAudit_AddComment,
    [AdminAuditActionEnum.ADD_PAPER_OWNER]: AdminAudit_AddPaperOwner,
    [AdminAuditActionEnum.ADD_PAPER_OWNER_2]: AdminAudit_AddPaperOwner2,
    [AdminAuditActionEnum.CHANGE_PAPER_PW]: AdminAudit_ChangePaperPassword,
    [AdminAuditActionEnum.ARXIV_MAKE_AUTHOR]: AdminAudit_AdminMakeAuthor,
    [AdminAuditActionEnum.ARXIV_MAKE_NONAUTHOR]: AdminAudit_AdminMakeNonauthor,
    [AdminAuditActionEnum.ARXIV_REVOKE_PAPER_OWNER]: AdminAudit_AdminRevokePaperOwner,
    [AdminAuditActionEnum.ARXIV_UNREVOKE_PAPER_OWNER]: AdminAudit_AdminUnrevokePaperOwner,
    [AdminAuditActionEnum.BECOME_USER]: AdminAudit_BecomeUser,
    [AdminAuditActionEnum.CHANGE_EMAIL]: AdminAudit_ChangeEmail,
    [AdminAuditActionEnum.CHANGE_PASSWORD]: AdminAudit_ChangePassword,
    [AdminAuditActionEnum.ENDORSED_BY_SUSPECT]: AdminAudit_EndorsedBySuspect,
    [AdminAuditActionEnum.GOT_NEGATIVE_ENDORSEMENT]: AdminAudit_GotNegativeEndorsement,
    [AdminAuditActionEnum.MAKE_MODERATOR]: AdminAudit_MakeModerator,
    [AdminAuditActionEnum.UNMAKE_MODERATOR]: AdminAudit_UnmakeModerator,
    [AdminAuditActionEnum.SUSPEND_USER]: AdminAudit_SuspendUser,
    [AdminAuditActionEnum.UNSUSPEND_USER]: AdminAudit_UnsuspendUser,
    [AdminAuditActionEnum.ARXIV_CHANGE_STATUS]: AdminAudit_ChangeStatus,
    [AdminAuditActionEnum.ARXIV_CHANGE_PAPER_PW]: AdminAudit_AdminChangePaperPassword,
    [AdminAuditActionEnum.REVOKE_PAPER_OWNER]: AdminAudit_RevokePaperOwner,
    [AdminAuditActionEnum.FLIP_FLAG]: adminAuditFlipFlagInstantiator,
};

export function createAdminAuditEvent(auditRecord: RaRecord<Identifier>): AdminAuditEvent {
    const eventClassOrFactory = eventClasses[auditRecord.action];
    if (!eventClassOrFactory) {
        throw new Error(`${auditRecord.action} is not a valid admin action`);
    }

    // Check if it's the flip flag factory function
    if (auditRecord.action === AdminAuditActionEnum.FLIP_FLAG) {
        return adminAuditFlipFlagInstantiator(auditRecord as TapirAdminAudit);
    }

    // It's a class constructor
    const EventClass = eventClassOrFactory as typeof AdminAuditEvent;
    const params = EventClass.getInitParams(auditRecord as TapirAdminAudit);
    const { admin_user, affected_user, session_id, ...options } = params;
    return new (EventClass as any)(admin_user, affected_user, session_id, options);
}