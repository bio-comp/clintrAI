# ClinicalTrials.gov API - Single Study Endpoint

## GET /studies/{nctId}

Returns data of a single study.

**API Server:** `https://beta-ut.clinicaltrials.gov/api/v2`  
**Authentication:** Not Required

## Request Parameters

### Path Parameters

| Parameter | Type | Required | Description | Examples |
|-----------|------|----------|-------------|----------|
| `nctId` | string | Yes | NCT Number of a study. If found in NCTIdAlias field, 301 HTTP redirect to the actual study will be returned. | `NCT00841061`, `NCT04000165` |

**Pattern:** `^[Nn][Cc][Tt]0*[1-9]\d{0,7}$`

### Query String Parameters

| Parameter | Type | Default | Description | Examples |
|-----------|------|---------|-------------|----------|
| `format` | enum | `json` | Output format | See format options below |
| `markupFormat` | enum | `markdown` | Format of markup type fields. Applicable only to json format. | `markdown`, `legacy` |
| `fields` | array of string | | Specific fields to return. If unspecified, all fields returned | `["NCTId", "BriefTitle", "Reference"]`, `["ConditionsModule", "EligibilityModule"]` |

#### Format Options

| Value | Description |
|-------|-------------|
| `csv` | Return CSV table; available fields are listed on CSV Download |
| `json` | Return JSON object; format of markup fields depends on markupFormat parameter |
| `json.zip` | Put JSON object into a .json file and download it as zip archive; field values of type markup are in markdown format |
| `fhir.json` | Return FHIR JSON; fields are not customizable; see Access Data in FHIR |
| `ris` | Return RIS record; available tags are listed on RIS Download |

#### Markup Format Options

| Value | Description |
|-------|-------------|
| `markdown` | Markdown format |
| `legacy` | Compatible with classic PRS |

#### Fields Parameter Details

**For csv format:** Specify list of columns. Column names are available on CSV Download.

**For json and json.zip formats:** Every list item is either area name, piece name, or field name. If a piece or a field is a branch node, all descendant fields will be included. All area names are available on Search Areas, the piece and field names on Data Structure and also can be retrieved at `/studies/metadata` endpoint.

**For fhir.json format:** All available fields are returned and this parameter must be unspecified.

**For ris format:** Specify list of tags. Tag names are available on RIS Download.

## Response Format

### JSON Response Structure

```json
{
  "protocolSection": {
    "identificationModule": {
      "nctId": "AAAAAAAAAAA",
      "nctIdAliases": ["AAAAAAAAAAA"],
      "orgStudyIdInfo": {
        "id": "string",
        "type": "NIH",
        "link": "string"
      },
      "secondaryIdInfos": [
        {
          "id": "string",
          "type": "NIH",
          "domain": "string",
          "link": "string"
        }
      ],
      "briefTitle": "string",
      "officialTitle": "string",
      "acronym": "string",
      "organization": {
        "fullName": "string",
        "class": "NIH"
      }
    },
    "statusModule": {
      "statusVerifiedDate": "string",
      "overallStatus": "ACTIVE_NOT_RECRUITING",
      "lastKnownStatus": "ACTIVE_NOT_RECRUITING",
      "delayedPosting": false,
      "whyStopped": "string",
      "expandedAccessInfo": {
        "hasExpandedAccess": false,
        "nctId": "AAAAAAAAAAA",
        "statusForNctId": "AVAILABLE"
      },
      "startDateStruct": {
        "date": "string",
        "type": "ACTUAL"
      },
      "primaryCompletionDateStruct": {
        "date": "string",
        "type": "ACTUAL"
      },
      "completionDateStruct": {
        "date": "string",
        "type": "ACTUAL"
      },
      "studyFirstSubmitDate": "1970-01-01",
      "studyFirstSubmitQcDate": "1970-01-01",
      "studyFirstPostDateStruct": {
        "date": "1970-01-01",
        "type": "ACTUAL"
      },
      "resultsWaived": false,
      "resultsFirstSubmitDate": "1970-01-01",
      "resultsFirstSubmitQcDate": "1970-01-01",
      "resultsFirstPostDateStruct": {
        "date": "1970-01-01",
        "type": "ACTUAL"
      },
      "dispFirstSubmitDate": "1970-01-01",
      "dispFirstSubmitQcDate": "1970-01-01",
      "dispFirstPostDateStruct": {
        "date": "1970-01-01",
        "type": "ACTUAL"
      },
      "lastUpdateSubmitDate": "1970-01-01",
      "lastUpdatePostDateStruct": {
        "date": "1970-01-01",
        "type": "ACTUAL"
      }
    },
    "sponsorCollaboratorsModule": {
      "responsibleParty": {
        "type": "SPONSOR",
        "investigatorFullName": "string",
        "investigatorTitle": "string",
        "investigatorAffiliation": "string",
        "oldNameTitle": "string",
        "oldOrganization": "string"
      },
      "leadSponsor": {
        "name": "string",
        "class": "NIH"
      },
      "collaborators": [
        {
          "name": "string",
          "class": "NIH"
        }
      ]
    },
    "oversightModule": {
      "oversightHasDmc": false,
      "isFdaRegulatedDrug": false,
      "isFdaRegulatedDevice": false,
      "isUnapprovedDevice": false,
      "isPpsd": false,
      "isUsExport": false,
      "fdaaa801Violation": false
    },
    "descriptionModule": {
      "briefSummary": "string",
      "detailedDescription": "string"
    },
    "conditionsModule": {
      "conditions": ["string"],
      "keywords": ["string"]
    },
    "designModule": {
      "studyType": "EXPANDED_ACCESS",
      "nPtrsToThisExpAccNctId": 0,
      "expandedAccessTypes": {
        "individual": false,
        "intermediate": false,
        "treatment": false
      },
      "patientRegistry": false,
      "targetDuration": "0 Year",
      "phases": ["NA"],
      "designInfo": {
        "allocation": "RANDOMIZED",
        "interventionModel": "SINGLE_GROUP",
        "interventionModelDescription": "string",
        "primaryPurpose": "TREATMENT",
        "observationalModel": "COHORT",
        "timePerspective": "RETROSPECTIVE",
        "maskingInfo": {
          "masking": "NONE",
          "maskingDescription": "string",
          "whoMasked": ["PARTICIPANT"]
        }
      },
      "bioSpec": {
        "retention": "NONE_RETAINED",
        "description": "string"
      },
      "enrollmentInfo": {
        "count": 0,
        "type": "ACTUAL"
      }
    },
    "armsInterventionsModule": {
      "armGroups": [
        {
          "label": "string",
          "type": "EXPERIMENTAL",
          "description": "string",
          "interventionNames": ["string"]
        }
      ],
      "interventions": [
        {
          "type": "BEHAVIORAL",
          "name": "string",
          "description": "string",
          "armGroupLabels": ["string"],
          "otherNames": ["string"]
        }
      ]
    },
    "outcomesModule": {
      "primaryOutcomes": [
        {
          "measure": "string",
          "description": "string",
          "timeFrame": "string"
        }
      ],
      "secondaryOutcomes": [
        {
          "measure": "string",
          "description": "string",
          "timeFrame": "string"
        }
      ],
      "otherOutcomes": [
        {
          "measure": "string",
          "description": "string",
          "timeFrame": "string"
        }
      ]
    },
    "eligibilityModule": {
      "eligibilityCriteria": "string",
      "healthyVolunteers": false,
      "sex": "FEMALE",
      "genderBased": false,
      "genderDescription": "string",
      "minimumAge": "0 Year",
      "maximumAge": "0 Year",
      "stdAges": ["CHILD"],
      "studyPopulation": "string",
      "samplingMethod": "PROBABILITY_SAMPLE"
    },
    "contactsLocationsModule": {
      "centralContacts": [
        {
          "name": "string",
          "role": "STUDY_CHAIR",
          "phone": "string",
          "phoneExt": "string",
          "email": "string"
        }
      ],
      "overallOfficials": [
        {
          "name": "string",
          "affiliation": "string",
          "role": "STUDY_CHAIR"
        }
      ],
      "locations": [
        {
          "facility": "string",
          "status": "ACTIVE_NOT_RECRUITING",
          "city": {},
          "state": {},
          "zip": "string",
          "country": "string",
          "contacts": [
            {
              "name": "string",
              "role": "STUDY_CHAIR",
              "phone": "string",
              "phoneExt": "string",
              "email": "string"
            }
          ],
          "geoPoint": {
            "lat": 0,
            "lon": 0
          }
        }
      ]
    },
    "referencesModule": {
      "references": [
        {
          "pmid": "string",
          "type": "BACKGROUND",
          "citation": "string",
          "retractions": [
            {
              "pmid": "string",
              "source": "string"
            }
          ]
        }
      ],
      "seeAlsoLinks": [
        {
          "label": "string",
          "url": "string"
        }
      ],
      "availIpds": [
        {
          "id": "string",
          "type": "string",
          "url": "string",
          "comment": "string"
        }
      ]
    },
    "ipdSharingStatementModule": {
      "ipdSharing": "YES",
      "description": "string",
      "infoTypes": ["STUDY_PROTOCOL"],
      "timeFrame": "string",
      "accessCriteria": "string",
      "url": "string"
    }
  },
  "resultsSection": {
    "participantFlowModule": {
      "preAssignmentDetails": "string",
      "recruitmentDetails": "string",
      "typeUnitsAnalyzed": "string",
      "groups": [
        {
          "id": "string",
          "title": "string",
          "description": "string"
        }
      ],
      "periods": [
        {
          "title": "string",
          "milestones": [
            {
              "type": "string",
              "comment": "string",
              "achievements": [
                {
                  "groupId": "string",
                  "comment": "string",
                  "numSubjects": "string",
                  "numUnits": "string"
                }
              ]
            }
          ],
          "dropWithdraws": [
            {
              "type": "string",
              "comment": "string",
              "reasons": [
                {
                  "groupId": "string",
                  "comment": "string",
                  "numSubjects": "string",
                  "numUnits": "string"
                }
              ]
            }
          ]
        }
      ]
    },
    "baselineCharacteristicsModule": {
      "populationDescription": "string",
      "typeUnitsAnalyzed": "string",
      "groups": [
        {
          "id": "string",
          "title": "string",
          "description": "string"
        }
      ],
      "denoms": [
        {
          "units": "string",
          "counts": [
            {
              "groupId": "string",
              "value": "string"
            }
          ]
        }
      ],
      "measures": [
        {
          "title": "string",
          "description": "string",
          "populationDescription": "string",
          "paramType": "GEOMETRIC_MEAN",
          "dispersionType": "NA",
          "unitOfMeasure": "string",
          "calculatePct": false,
          "denomUnitsSelected": "string",
          "denoms": [
            {
              "units": "string",
              "counts": [
                {
                  "groupId": "string",
                  "value": "string"
                }
              ]
            }
          ],
          "classes": [
            {
              "title": "string",
              "denoms": [
                {
                  "units": "string",
                  "counts": [
                    {
                      "groupId": "string",
                      "value": "string"
                    }
                  ]
                }
              ],
              "categories": [
                {
                  "title": "string",
                  "measurements": [
                    {
                      "groupId": "string",
                      "value": "string",
                      "spread": "string",
                      "lowerLimit": "string",
                      "upperLimit": "string",
                      "comment": "string"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    },
    "outcomeMeasuresModule": {
      "outcomeMeasures": [
        {
          "type": "PRIMARY",
          "title": "string",
          "description": "string",
          "populationDescription": "string",
          "reportingStatus": "NOT_POSTED",
          "anticipatedPostingDate": "string",
          "paramType": "GEOMETRIC_MEAN",
          "dispersionType": "string",
          "unitOfMeasure": "string",
          "calculatePct": false,
          "timeFrame": "string",
          "typeUnitsAnalyzed": "string",
          "denomUnitsSelected": "string",
          "groups": [
            {
              "id": "string",
              "title": "string",
              "description": "string"
            }
          ],
          "denoms": [
            {
              "units": "string",
              "counts": [
                {
                  "groupId": "string",
                  "value": "string"
                }
              ]
            }
          ],
          "classes": [
            {
              "title": "string",
              "denoms": [
                {
                  "units": "string",
                  "counts": [
                    {
                      "groupId": "string",
                      "value": "string"
                    }
                  ]
                }
              ],
              "categories": [
                {
                  "title": "string",
                  "measurements": [
                    {
                      "groupId": "string",
                      "value": "string",
                      "spread": "string",
                      "lowerLimit": "string",
                      "upperLimit": "string",
                      "comment": "string"
                    }
                  ]
                }
              ]
            }
          ],
          "analyses": [
            {
              "paramType": "string",
              "paramValue": "string",
              "dispersionType": "STANDARD_DEVIATION",
              "dispersionValue": "string",
              "statisticalMethod": "string",
              "statisticalComment": "string",
              "pValue": "string",
              "pValueComment": "string",
              "ciNumSides": "ONE_SIDED",
              "ciPctValue": "string",
              "ciLowerLimit": "string",
              "ciUpperLimit": "string",
              "ciLowerLimitComment": "string",
              "ciUpperLimitComment": "string",
              "estimateComment": "string",
              "testedNonInferiority": false,
              "nonInferiorityType": "SUPERIORITY",
              "nonInferiorityComment": "string",
              "otherAnalysisDescription": "string",
              "groupDescription": "string",
              "groupIds": ["string"]
            }
          ]
        }
      ]
    },
    "adverseEventsModule": {
      "frequencyThreshold": "string",
      "timeFrame": "string",
      "description": "string",
      "allCauseMortalityComment": "string",
      "eventGroups": [
        {
          "id": "string",
          "title": "string",
          "description": "string",
          "deathsNumAffected": 0,
          "deathsNumAtRisk": 0,
          "seriousNumAffected": 0,
          "seriousNumAtRisk": 0,
          "otherNumAffected": 0,
          "otherNumAtRisk": 0
        }
      ],
      "seriousEvents": [
        {
          "term": "string",
          "organSystem": "string",
          "sourceVocabulary": "string",
          "assessmentType": "NON_SYSTEMATIC_ASSESSMENT",
          "notes": "string",
          "stats": [
            {
              "groupId": "string",
              "numEvents": 0,
              "numAffected": 0,
              "numAtRisk": 0
            }
          ]
        }
      ],
      "otherEvents": [
        {
          "term": "string",
          "organSystem": "string",
          "sourceVocabulary": "string",
          "assessmentType": "NON_SYSTEMATIC_ASSESSMENT",
          "notes": "string",
          "stats": [
            {
              "groupId": "string",
              "numEvents": 0,
              "numAffected": 0,
              "numAtRisk": 0
            }
          ]
        }
      ]
    },
    "moreInfoModule": {
      "limitationsAndCaveats": {
        "description": "string"
      },
      "certainAgreement": {
        "piSponsorEmployee": false,
        "restrictionType": "LTE60",
        "restrictiveAgreement": false,
        "otherDetails": "string"
      },
      "pointOfContact": {
        "title": "string",
        "organization": "string",
        "email": "string",
        "phone": "string",
        "phoneExt": "string"
      }
    }
  },
  "annotationSection": {
    "annotationModule": {
      "unpostedAnnotation": {
        "unpostedResponsibleParty": "string",
        "unpostedEvents": [
          {
            "type": "RESET",
            "date": "1970-01-01",
            "dateUnknown": false
          }
        ]
      },
      "violationAnnotation": {
        "violationEvents": [
          {
            "type": "VIOLATION_IDENTIFIED",
            "description": "string",
            "creationDate": "1970-01-01",
            "issuedDate": "1970-01-01",
            "releaseDate": "1970-01-01",
            "postedDate": "1970-01-01"
          }
        ]
      }
    }
  },
  "documentSection": {
    "largeDocumentModule": {
      "noSap": false,
      "largeDocs": [
        {
          "typeAbbrev": "string",
          "hasProtocol": false,
          "hasSap": false,
          "hasIcf": false,
          "label": "string",
          "date": "1970-01-01",
          "uploadDate": "string",
          "filename": "string",
          "size": 0
        }
      ]
    }
  },
  "derivedSection": {
    "miscInfoModule": {
      "versionHolder": "1970-01-01",
      "removedCountries": ["string"],
      "submissionTracking": {
        "estimatedResultsFirstSubmitDate": "1970-01-01",
        "firstMcpInfo": {
          "postDateStruct": {
            "date": "1970-01-01",
            "type": "ACTUAL"
          }
        },
        "submissionInfos": [
          {
            "releaseDate": "1970-01-01",
            "unreleaseDate": "1970-01-01",
            "unreleaseDateUnknown": false,
            "resetDate": "1970-01-01",
            "mcpReleaseN": 0
          }
        ]
      }
    },
    "conditionBrowseModule": {
      "meshes": [
        {
          "id": "string",
          "term": "string"
        }
      ],
      "ancestors": [
        {
          "id": "string",
          "term": "string"
        }
      ],
      "browseLeaves": [
        {
          "id": "string",
          "name": "string",
          "asFound": "string",
          "relevance": "LOW"
        }
      ],
      "browseBranches": [
        {
          "abbrev": "string",
          "name": "string"
        }
      ]
    },
    "interventionBrowseModule": {
      "meshes": [
        {
          "id": "string",
          "term": "string"
        }
      ],
      "ancestors": [
        {
          "id": "string",
          "term": "string"
        }
      ],
      "browseLeaves": [
        {
          "id": "string",
          "name": "string",
          "asFound": "string",
          "relevance": "LOW"
        }
      ],
      "browseBranches": [
        {
          "abbrev": "string",
          "name": "string"
        }
      ]
    }
  },
  "hasResults": false
}
```

## Usage Examples

### Get Study in JSON Format
```
GET /studies/NCT04000165
```

### Get Study with Specific Fields
```
GET /studies/NCT04000165?fields=NCTId,BriefTitle,OverallStatus
```

### Get Study in CSV Format
```
GET /studies/NCT04000165?format=csv&fields=NCTId,BriefTitle,OverallStatus
```

### Get Study as FHIR JSON
```
GET /studies/NCT04000165?format=fhir.json
```

### Get Study with Legacy Markup Format
```
GET /studies/NCT04000165?markupFormat=legacy
```

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Study data returned successfully |
| 301 | Redirect - NCT ID found in NCTIdAlias field, redirects to actual study |
| 404 | Not Found - Study with specified NCT ID does not exist |
