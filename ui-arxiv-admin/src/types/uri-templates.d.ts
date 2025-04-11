
declare module 'uri-templates' {
    export default function uriTemplate(template: string): {
        fill: (params: Record<string, string | number | boolean>) => string;
        fillFromObject: (params: Record<string, any>) => string;
        varNames: string[];
    };
}
