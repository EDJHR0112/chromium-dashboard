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
import type { SurveyAnswers } from './SurveyAnswers';
import {
    SurveyAnswersFromJSON,
    SurveyAnswersFromJSONTyped,
    SurveyAnswersToJSON,
} from './SurveyAnswers';

/**
 * 
 * @export
 * @interface Gate
 */
export interface Gate {
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    id?: number;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    feature_id?: number;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    stage_id?: number;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    gate_type?: number;
    /**
     * 
     * @type {string}
     * @memberof Gate
     */
    team_name?: string;
    /**
     * 
     * @type {string}
     * @memberof Gate
     */
    gate_name?: string;
    /**
     * 
     * @type {string}
     * @memberof Gate
     */
    escalation_email?: string;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    state?: number;
    /**
     * 
     * @type {Date}
     * @memberof Gate
     */
    requested_on?: Date;
    /**
     * 
     * @type {Date}
     * @memberof Gate
     */
    responded_on?: Date;
    /**
     * 
     * @type {Array<string>}
     * @memberof Gate
     */
    assignee_emails?: Array<string>;
    /**
     * 
     * @type {string}
     * @memberof Gate
     */
    next_action?: string;
    /**
     * 
     * @type {boolean}
     * @memberof Gate
     */
    additional_review?: boolean;
    /**
     * DEFAULT_SLO_LIMIT is 5 in approval_defs.py
     * @type {number}
     * @memberof Gate
     */
    slo_initial_response?: number;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    slo_initial_response_took?: number;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    slo_initial_response_remaining?: number;
    /**
     * DEFAULT_SLO_RESOLVE_LIMIT is 10 in approval_defs.py
     * @type {number}
     * @memberof Gate
     */
    slo_resolve?: number;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    slo_resolve_took?: number;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    slo_resolve_remaining?: number;
    /**
     * 
     * @type {Date}
     * @memberof Gate
     */
    needs_work_started_on?: Date;
    /**
     * 
     * @type {Array<string>}
     * @memberof Gate
     */
    possible_assignee_emails?: Array<string>;
    /**
     * 
     * @type {boolean}
     * @memberof Gate
     */
    self_certify_eligible?: boolean;
    /**
     * 
     * @type {boolean}
     * @memberof Gate
     */
    self_certify_possible?: boolean;
    /**
     * 
     * @type {SurveyAnswers}
     * @memberof Gate
     */
    survey_answers?: SurveyAnswers;
    /**
     * 
     * @type {number}
     * @memberof Gate
     */
    earliest_milestone?: number;
}

/**
 * Check if a given object implements the Gate interface.
 */
export function instanceOfGate(value: object): value is Gate {
    return true;
}

export function GateFromJSON(json: any): Gate {
    return GateFromJSONTyped(json, false);
}

export function GateFromJSONTyped(json: any, ignoreDiscriminator: boolean): Gate {
    if (json == null) {
        return json;
    }
    return {
        
        'id': json['id'] == null ? undefined : json['id'],
        'feature_id': json['feature_id'] == null ? undefined : json['feature_id'],
        'stage_id': json['stage_id'] == null ? undefined : json['stage_id'],
        'gate_type': json['gate_type'] == null ? undefined : json['gate_type'],
        'team_name': json['team_name'] == null ? undefined : json['team_name'],
        'gate_name': json['gate_name'] == null ? undefined : json['gate_name'],
        'escalation_email': json['escalation_email'] == null ? undefined : json['escalation_email'],
        'state': json['state'] == null ? undefined : json['state'],
        'requested_on': json['requested_on'] == null ? undefined : (new Date(json['requested_on'])),
        'responded_on': json['responded_on'] == null ? undefined : (new Date(json['responded_on'])),
        'assignee_emails': json['assignee_emails'] == null ? undefined : json['assignee_emails'],
        'next_action': json['next_action'] == null ? undefined : json['next_action'],
        'additional_review': json['additional_review'] == null ? undefined : json['additional_review'],
        'slo_initial_response': json['slo_initial_response'] == null ? undefined : json['slo_initial_response'],
        'slo_initial_response_took': json['slo_initial_response_took'] == null ? undefined : json['slo_initial_response_took'],
        'slo_initial_response_remaining': json['slo_initial_response_remaining'] == null ? undefined : json['slo_initial_response_remaining'],
        'slo_resolve': json['slo_resolve'] == null ? undefined : json['slo_resolve'],
        'slo_resolve_took': json['slo_resolve_took'] == null ? undefined : json['slo_resolve_took'],
        'slo_resolve_remaining': json['slo_resolve_remaining'] == null ? undefined : json['slo_resolve_remaining'],
        'needs_work_started_on': json['needs_work_started_on'] == null ? undefined : (new Date(json['needs_work_started_on'])),
        'possible_assignee_emails': json['possible_assignee_emails'] == null ? undefined : json['possible_assignee_emails'],
        'self_certify_eligible': json['self_certify_eligible'] == null ? undefined : json['self_certify_eligible'],
        'self_certify_possible': json['self_certify_possible'] == null ? undefined : json['self_certify_possible'],
        'survey_answers': json['survey_answers'] == null ? undefined : SurveyAnswersFromJSON(json['survey_answers']),
        'earliest_milestone': json['earliest_milestone'] == null ? undefined : json['earliest_milestone'],
    };
}

export function GateToJSON(value?: Gate | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'id': value['id'],
        'feature_id': value['feature_id'],
        'stage_id': value['stage_id'],
        'gate_type': value['gate_type'],
        'team_name': value['team_name'],
        'gate_name': value['gate_name'],
        'escalation_email': value['escalation_email'],
        'state': value['state'],
        'requested_on': value['requested_on'] == null ? undefined : ((value['requested_on']).toISOString()),
        'responded_on': value['responded_on'] == null ? undefined : ((value['responded_on']).toISOString()),
        'assignee_emails': value['assignee_emails'],
        'next_action': value['next_action'],
        'additional_review': value['additional_review'],
        'slo_initial_response': value['slo_initial_response'],
        'slo_initial_response_took': value['slo_initial_response_took'],
        'slo_initial_response_remaining': value['slo_initial_response_remaining'],
        'slo_resolve': value['slo_resolve'],
        'slo_resolve_took': value['slo_resolve_took'],
        'slo_resolve_remaining': value['slo_resolve_remaining'],
        'needs_work_started_on': value['needs_work_started_on'] == null ? undefined : ((value['needs_work_started_on']).toISOString()),
        'possible_assignee_emails': value['possible_assignee_emails'],
        'self_certify_eligible': value['self_certify_eligible'],
        'self_certify_possible': value['self_certify_possible'],
        'survey_answers': SurveyAnswersToJSON(value['survey_answers']),
        'earliest_milestone': value['earliest_milestone'],
    };
}

