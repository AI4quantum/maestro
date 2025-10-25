/*
Copyright 2025.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// WorkflowRun
type WorkflowRunSpec struct {
	// Important: Run "make" to regenerate code after modifying this file

	Agents       []string `json:"agents,omitempty" yaml:"agents,omitempty"`
	Workflow     string   `json:"workflow,omitempty" yaml:"workflow,omitempty"`
	LogLevel     string   `json:"loglevel,omitempty" yaml:"loglevel,omitempty"`
	Secrets      string   `json:"secrets,omitempty" yaml:"secrets,omitempty"`
	Environments string   `json:"environments,omitempty" yaml:"environments,omitempty"`
	NodePort     int32    `json:"nodeport,omitempty" yaml:"nodeport,omitempty"`
}

type WorkflowRunStatus struct {
	Conditions []metav1.Condition `json:"conditions,omitempty" patchStrategy:"merge" patchMergeKey:"type" protobuf:"bytes,1,rep,name=conditions"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status

type WorkflowRun struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty" json:"metadata,omitempty"`

	Spec   WorkflowRunSpec   `json:"spec,omitempty" yaml:"spec,omitempty"`
	Status WorkflowRunStatus `json:"status,omitempty" yaml:"status,omitempty"`
}

// +kubebuilder:object:root=true

type WorkflowRunList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty" yaml:"metadata,omitempty"`
	Items           []WorkflowRun `json:"items"`
}

// Workflow


type Input struct {
	Prompt   string `json:"prompt,omitempty" yaml:"prompt,omitempty"`
	Template string `json:"template,omitempty" yaml:"template,omitempty"`
}
type Loop struct {
	Agent string `json:"agent,omitempty" yaml:"agent,omitempty"`
	Until string `json:"until,omitempty" yaml:"until,omitempty"`
}
type Condition struct {
	If      string `json:"if,omitempty" yaml:"if,omitempty"`
	Then    string `json:"then,omitempty" yaml:"then,omitempty"`
	Else    string `json:"else,omitempty" yaml:"else,omitempty"`
	Case    string `json:"case,omitempty" yaml:"case,omitempty"`
	Do      string `json:"do,omitempty" yaml:"do,omitempty"`
	Default string `json:"default,omitempty" yaml:"default,omitempty"`
}

//	type Parallel struct {
//		Agent string `json:"agent,omitempty"` // ???
//	}
type Step struct {
	Name      string      `json:"name,omitempty" yaml:"name,omitempty"`
	Agent     string      `json:"agent,omitempty" yaml:"agent,omitempty"`
	From      string      `json:"from,omitempty" yaml:"from,omitempty"`
	Context   []string    `json:"context,omitempty" yaml:"context,omitempty"`
	Input     Input       `json:"input,omitempty" yaml:"input,omitempty"`
	Loop      Loop        `json:"loop,omitempty" yaml:"loop,omitempty"`
	Condition []Condition `json:"condition,omitempty" yaml:"condition,omitempty"`
	Parallel  []string    `json:"parallel,omitempty" yaml:"parallel,omitempty"`
}
type Exception struct {
	Name  string `json:"name,omitempty" yaml:"name,omitempty"`
	Agent string `json:"agent,omitempty" yaml:"agent,omitempty"`
}

type Event struct {
	Cron  string   `json:"cron,omitempty" yaml:"cron,omitempty"`
	Name  string   `json:"name,omitempty" yaml:"name,omitempty"`
	Agent string   `json:"agent,omitempty" yaml:"agent,omitempty"`
	Steps []string `json:"steps,omitempty" yaml:"steps,omitempty"`
	Exit  string   `json:"exit,omitempty" yaml:"exit,omitempty"`
}

type Template struct {
	// Important: Run "make" to regenerate code after modifying this file
	metav1.ObjectMeta `json:"metadata,omitempty" yaml:"metadata,omitempty"`

	Event     Event     `json:"event,omitempty" yaml:"event,omitempty"`
	Agents    []string  `json:"agents,omitempty" yaml:"agents,omitempty"`
	Exception Exception `json:"exception,omitempty" yaml:"exception,omitempty"`
	Prompt    string    `json:"prompt,omitempty" yaml:"prompt,omitempty"`
	Steps     []Step    `json:"steps,omitempty" yaml:"steps,omitempty"`
}

type WorkflowSpec struct {
	Template Template `json:"template,omitempty" yaml:"template,omitempty"`
}

type WorkflowStatus struct {
	// INSERT ADDITIONAL STATUS FIELD - define observed state of cluster
	// Important: Run "make" to regenerate code after modifying this file
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status

type Workflow struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty" yaml:"metadata,omitempty"`

	Spec   WorkflowSpec   `json:"spec,omitempty" yaml:"spec,omitempty"`
	Status WorkflowStatus `json:"status,omitempty" yaml:"status,omitempty"`
}

// +kubebuilder:object:root=true

type WorkflowList struct {
	metav1.TypeMeta `yaml:",inline"`
	metav1.ListMeta `json:"metadata,omitempty" yaml:"metadata,omitempty"`
	Items           []Workflow `json:"items"`
}

// Agent
// +kubebuilder:validation:Type=object
type ModelParameters struct {
	MaxTokens        *int      `json:"max_tokens,omitempty" yaml:"max_tokens,omitempty"`
	// +kubebuilder:validation:Type=number
	Temperature      *float64  `json:"temperature,omitempty" yaml:"temperature,omitempty"`
	TopK             *int      `json:"top_k,omitempty" yaml:"top_k,omitempty"`
	// +kubebuilder:validation:Type=number
	TopP             *float64  `json:"top_p,omitempty" yaml:"top_p,omitempty"`
	// +kubebuilder:validation:Type=number
	FrequencyPenalty *float64  `json:"frequency_penalty,omitempty" yaml:"frequency_penalty,omitempty"`
	// +kubebuilder:validation:Type=number
	PresencePenalty  *float64  `json:"presence_penalty,omitempty" yaml:"presence_penalty,omitempty"`
	StopSequences    []string  `json:"stop_sequences,omitempty" yaml:"stop_sequences,omitempty"`
}

type AgentSpec struct {
	// Important: Run "make" to regenerate code after modifying this file

	Description     string            `json:"description,omitempty" yaml:"description,omitempty"`
	Model           string            `json:"model,omitempty" yaml:"model,omitempty"`
	Framework       string            `json:"framework,omitempty" yaml:"framework,omitempty"`
	Mode            string            `json:"mode,omitempty" yaml:"mode,omitempty"`
	Tools           []string          `json:"tools,omitempty" yaml:"tools,omitempty"`
	Instructions    string            `json:"instructions,omitempty" yaml:"instructions,omitempty"`
	Code            string            `json:"code,omitempty" yaml:"code,omitempty"`
	Input           string            `json:"input,omitempty" yaml:"input,omitempty"`
	Output          string            `json:"oputput,omitempty" yaml:"oputput,omitempty"`
	Url             string            `json:"url,omitempty" yaml:"url,omitempty"`
	ModelParameters *ModelParameters  `json:"model_parameters,omitempty" yaml:"model_parameters,omitempty"`
}

type AgentStatus struct {
	// INSERT ADDITIONAL STATUS FIELD - define observed state of cluster
	// Important: Run "make" to regenerate code after modifying this file
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status

type Agent struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty" yaml:"metadata,omitempty"`

	Spec   AgentSpec   `json:"spec,omitempty" yaml:"spec,omitempty"`
	Status AgentStatus `json:"status,omitempty" yaml:"status,omitempty"`
}

// +kubebuilder:object:root=true

type AgentList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty" yaml:"metadata,omitempty"`
	Items           []Agent `json:"items"`
}

func init() {
	SchemeBuilder.Register(&WorkflowRun{}, &WorkflowRunList{})
	SchemeBuilder.Register(&Workflow{}, &WorkflowList{})
	SchemeBuilder.Register(&Agent{}, &AgentList{})
}
