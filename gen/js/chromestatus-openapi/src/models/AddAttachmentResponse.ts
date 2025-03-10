/* tslint:disable */
/* eslint-disable */
/**
 * chomestatus API
 * The API for chromestatus.com. chromestatus.com is the official tool used for tracking feature launches in Blink (the browser engine that powers Chrome and many other web browsers). This tool guides feature owners through our launch process and serves as a primary source for developer information that then ripples throughout the web developer ecosystem. More details at: https://github.com/GoogleChrome/chromium-dashboard
 *
 * The version of the OpenAPI document: 1.0.0
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { mapValues } from '../runtime';
/**
 * 
 * @export
 * @interface AddAttachmentResponse
 */
export interface AddAttachmentResponse {
    /**
     * 
     * @type {string}
     * @memberof AddAttachmentResponse
     */
    attachment_url?: string;
}

/**
 * Check if a given object implements the AddAttachmentResponse interface.
 */
export function instanceOfAddAttachmentResponse(value: object): value is AddAttachmentResponse {
    return true;
}

export function AddAttachmentResponseFromJSON(json: any): AddAttachmentResponse {
    return AddAttachmentResponseFromJSONTyped(json, false);
}

export function AddAttachmentResponseFromJSONTyped(json: any, ignoreDiscriminator: boolean): AddAttachmentResponse {
    if (json == null) {
        return json;
    }
    return {
        
        'attachment_url': json['attachment_url'] == null ? undefined : json['attachment_url'],
    };
}

export function AddAttachmentResponseToJSON(value?: AddAttachmentResponse | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'attachment_url': value['attachment_url'],
    };
}

