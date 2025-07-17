import logging
import re
from core.llm_interface import call_gemini

logger = logging.getLogger(__name__)

class VisualizeApiClient:
    def __init__(self):
        pass

    def _detect_language(self, text: str) -> str:
        """
        Detect if the text is in Vietnamese or English.
        Returns 'vietnamese' or 'english'.
        """
        # Vietnamese characters and common words
        vietnamese_chars = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE)
        vietnamese_words = ['của', 'và', 'là', 'có', 'được', 'cho', 'với', 'từ', 'này', 'đó', 'đây', 'kia', 'một', 'hai', 'ba', 'bốn', 'năm']
        
        # Check for Vietnamese characters
        if vietnamese_chars.search(text):
            return 'vietnamese'
        
        # Check for Vietnamese words
        text_lower = text.lower()
        vietnamese_word_count = sum(1 for word in vietnamese_words if word in text_lower)
        if vietnamese_word_count >= 2:  # If at least 2 Vietnamese words found
            return 'vietnamese'
        
        return 'english'

    def visualize(self, prompt: str, file_texts: list) -> dict:
        """
        Dedicated visualization service that generates BPMN diagrams from process descriptions.
        This service only handles visualization, not process improvement or bottleneck analysis.
        """
        # Detect language from user prompt
        detected_language = self._detect_language(prompt)
        logger.info(f"Detected language: {detected_language}")
        
        # Combine all file contents into a single string for context
        combined_file_content = ""
        for file_text in file_texts:
            combined_file_content += f"File Type: {file_text['file_type']}\n"
            combined_file_content += f"File Content:\n{file_text['file_content']}\n\n"
        
        # Create language-specific prompts
        if detected_language == 'vietnamese':
            visualization_prompt = f"""
            Dựa trên yêu cầu và nội dung tệp sau, hãy tạo một sơ đồ BPMN (Business Process Model and Notation) XML.
            
            Yêu cầu người dùng: {prompt}
            
            Nội dung tệp:
            {combined_file_content}
            
            Tạo một sơ đồ BPMN 2.0 XML hợp lệ thể hiện quy trình được mô tả. Đảm bảo cấu trúc này phản ánh các bên tham gia và luồng thông tin giữa họ. Bao gồm:
            1. Tên quy trình rõ ràng
            2. Các Pool (bể) và Lane (làn) để phân chia vai trò/bộ phận tham gia vào quy trình (ví dụ: Khách hàng, Ngân hàng, Phòng ban X, Y, Z). Đặt tên rõ ràng cho từng Pool và Lane.
            3. Các tác vụ/hoạt động tuần tự (tên của mỗi tác vụ và hoạt động phải ngắn gọn, từ 4-8 từ)
            4. Cổng cho các điểm quyết định và điều kiện (thêm để logic tốt hơn, ngay cả khi không có mô tả trong dữ liệu)
            5. Mũi tên kết nối các tác vụ/hoạt động trong cùng một làn (Sequence Flows). Thêm để logic tốt hơn, ngay cả khi không có mô tả trong dữ liệu, các tác vụ phải nối với nhau có logic hoặc nối với điểm kết thúc, không được có tác vụ không nối đến gì cả.
            6. **Các đường luồng thông điệp (Message Flows) để thể hiện sự trao đổi thông tin giữa các Pool hoặc Lane khác nhau, nếu có sự tương tác qua lại giữa chúng.**
            7. Sự kiện bắt đầu và kết thúc
            8. Cấu trúc BPMN XML phù hợp
            
            Trả về phản hồi theo định dạng JSON chính xác này:
            {{
                "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
                "diagram_name": "Tên Sơ Đồ Quy Trình",
                "diagram_description": "Mô tả rõ ràng về những gì sơ đồ này thể hiện",
                "detail_descriptions": {{
                    "Tên tác vụ 1": "Mô tả tác vụ đầu tiên",
                    "Tên tác vụ 2": "Mô tả tác vụ thứ hai"
                }}
            }}
            
            Đảm bảo BPMN XML hợp lệ và tuân theo tiêu chuẩn BPMN 2.0.
            """
        else:
            visualization_prompt = f"""
            Based on the following prompt and file content, generate a BPMN (Business Process Model and Notation) XML diagram.
            
            User Request: {prompt}
            
            File Content:
            {combined_file_content}
            
            Generate a valid BPMN 2.0 XML diagram that represents the process described. Ensure the diagram accurately reflects the participants (roles/departments) and the flow of information between them. Include the following BPMN elements:

            1.  A clear and concise process name.
            2.  Appropriate Pools and Lanes to clearly segment the process by participating roles or departments (e.g., "Customer," "Bank," "Department X"). Name each Pool and Lane distinctly.
            3.  Sequential tasks/activities within each Lane. The name of each task and activity should be concise, ideally between 4-8 words, and clearly describe the action.
            4.  Gateways for decision points and conditional branching (e.g., Exclusive Gateways for "yes/no" decisions, Parallel Gateways for concurrent activities). Add these for robust process logic, even if not explicitly detailed in the input data.
            5.  Sequence Flows (solid arrows) to connect tasks/activities logically within the same Lane. Ensure all tasks are connected to subsequent tasks, gateways, or an end event, preventing disconnected elements.
            6.  **Message Flows (dashed arrows) to illustrate the exchange of information or communication between different Pools or Lanes, where interactions across participants occur.**
            7.  Start and end events to define the beginning and termination points of the process.
            8.  A proper and well-structured BPMN XML compliant with BPMN 2.0 standards.
            

            Return the response in this exact JSON format:
            {{
                "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
                "diagram_name": "Process Name Diagram",
                "diagram_description": "A clear description of what this diagram represents",
                "detail_descriptions": {{
                    "Name of task 1": "Description of the first task",
                    "Name of task 2": "Description of the second task"
                }}
            }}
            
            Ensure the BPMN XML is valid and follows BPMN 2.0 standards.
            """
        
        try:
            response = call_gemini(visualization_prompt, temperature=0.2, max_output_tokens=65536)
            logger.info(f"Visualization_prompt: {visualization_prompt}")
            logger.info(f"Raw LLM response: {response}")
            
            # Try to extract JSON from the response
            import json
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response_json = json.loads(json_match.group())
                
                # Generate concise memory focusing on user preferences and diagram data
                file_types = ', '.join([ft['file_type'] for ft in file_texts])
                num_tasks = len(response_json.get("detail_descriptions", {}))
                diagram_name = response_json.get("diagram_name", "N/A")
                # Heuristic: extract special preferences from prompt
                preferences = []
                prompt_lower = prompt.lower()
                if "swimlane" in prompt_lower or "swim lane" in prompt_lower:
                    preferences.append("swimlane")
                if "highlight" in prompt_lower or "làm nổi bật" in prompt_lower:
                    preferences.append("highlighted steps")
                if "approval" in prompt_lower or "phê duyệt" in prompt_lower:
                    preferences.append("approval steps")
                if "color" in prompt_lower or "màu" in prompt_lower:
                    preferences.append("color coding")
                if not preferences:
                    preferences.append("standard")
                
                # Add language to memory for session consistency
                memory_content = (
                    f"Diagram: {diagram_name}; Tasks: {num_tasks}; File type(s): {file_types}; "
                    f"Preferences: {', '.join(preferences)}; Language: {detected_language}."
                )
                return {
                    "diagram_data": response_json.get("diagram_data", "<bpmn:definitions>...</bpmn:definitions>"),
                    "diagram_name": response_json.get("diagram_name", "Process Diagram"),
                    "Diagram_description": response_json.get("diagram_description", "Generated BPMN diagram"),
                    "detail_descriptions": response_json.get("detail_descriptions", {}),
                    "Memory": memory_content.strip()
                }
            else:
                # Fallback if JSON parsing fails
                logger.warning("Could not parse JSON from LLM response, using fallback")
                file_types = ', '.join([ft['file_type'] for ft in file_texts])
                preferences = []
                prompt_lower = prompt.lower()
                if "swimlane" in prompt_lower or "swim lane" in prompt_lower:
                    preferences.append("swimlane")
                if "highlight" in prompt_lower or "làm nổi bật" in prompt_lower:
                    preferences.append("highlighted steps")
                if "approval" in prompt_lower or "phê duyệt" in prompt_lower:
                    preferences.append("approval steps")
                if "color" in prompt_lower or "màu" in prompt_lower:
                    preferences.append("color coding")
                if not preferences:
                    preferences.append("standard")
                
                fallback_memory = (
                    f"Diagram: Generated Process Diagram; Tasks: 2; File type(s): {file_types}; "
                    f"Preferences: {', '.join(preferences)}; Language: {detected_language}."
                )
                return {
                    "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
                    "diagram_name": "Generated Process Diagram",
                    "Diagram_description": "BPMN diagram generated from process description",
                    "detail_descriptions": {"Task_1": "Process step 1", "Task_2": "Process step 2"},
                    "Memory": fallback_memory.strip()
                }
                
        except Exception as e:
            logger.error(f"Error in visualization service: {e}")
            error_memory = (
                f"Diagram: Error - Process Diagram; Tasks: 0; File type(s): {', '.join([ft['file_type'] for ft in file_texts])}; "
                f"Preferences: error; Language: {detected_language}."
            )
            # Return a basic fallback response
            return {
                "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
                "diagram_name": "Error - Process Diagram",
                "Diagram_description": "Error occurred during diagram generation",
                "detail_descriptions": {"Error": "Could not generate diagram"},
                "Memory": error_memory.strip()
            }