import { ref, computed } from 'vue';
// 规划数据状态
const skillTree = ref([]);
const jobMarketData = ref([]);
const selectedNode = ref(null);
const isLoading = ref(false);
// 进度追踪
const completedSkills = ref([]);
const learningProgress = ref(0);
// 生成规划
const generatePlan = async (major, goal) => {
 isLoading.value = true;
 try {
 const response = await fetch('/api/generate_plan', {
 method: 'POST',
 body: new URLSearchParams({ major, goal })
 });
 const data = await response.json();
 skillTree.value = data.skill_tree || [];
 jobMarketData.value = data.job_market || [];
 // 计算学习进度
 calculateProgress();
 return data;
 }
 finally {
 isLoading.value = false;
 }
};
// 选择节点
const selectNode = (node) => {
 selectedNode.value = node;
};
// 标记技能完成
const markSkillComplete = (skillId) => {
 if (!completedSkills.value.includes(skillId)) {
 completedSkills.value.push(skillId);
 calculateProgress();
 }
};
// 计算学习进度
const calculateProgress = () => {
 if (skillTree.value.length === 0) {
 learningProgress.value = 0;
 return;
 }
 let totalSkills = 0;
 const countSkills = (nodes) => {
 nodes.forEach(node => {
 totalSkills++;
 if (node.children && node.children.length > 0) {
 countSkills(node.children);
 }
 });
 };
 countSkills(skillTree.value);
 learningProgress.value = Math.round((completedSkills.value.length / totalSkills) * 100);
};
// 重置进度
const resetProgress = () => {
 completedSkills.value = [];
 learningProgress.value = 0;
};
// 导出状态和方法
export function usePlanStore() {
 return {
 // 状态
 skillTree: computed(() => skillTree.value),
 jobMarketData: computed(() => jobMarketData.value),
 selectedNode: computed(() => selectedNode.value),
 isLoading: computed(() => isLoading.value),
 completedSkills: computed(() => completedSkills.value),
 learningProgress: computed(() => learningProgress.value),
 // 方法
 generatePlan,
 selectNode,
 markSkillComplete,
 resetProgress
 };
}
export default { usePlanStore };
