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

    def _summarize_file_content(self, file_type: str, file_content: str, language: str) -> str:
        """
        Summarize the file content using the LLM, focusing on key components, steps, conditions, and their interactions.
        """
        if language == 'vietnamese':
            summary_prompt = f"""
            Tóm tắt nội dung tệp sau, trích xuất toàn bộ các thành phần chính, các bước, điều kiện và cách chúng tương tác với nhau. 
            Loại tệp: {file_type}
            Nội dung tệp:
            {file_content}
            """
        else:
            summary_prompt = f"""
            Based on the following "File Content", generate a detailed summary for the process in the file.

            Crucially, identify and list ALL distinct steps of the process as described in the file, from initiation to completion. Ensure that no intermediate steps are omitted, even if they seem minor.

            For each identified step, clearly include the following components:
            -   Step Number and Name: As provided or clearly implied by the file content (e.g., "2.2.1.1 Khai thác tìm kiếm khách hàng").
            -   Roles/Departments Involved: List the specific personnel or departments responsible for actions within that step (e.g., PFC, Loan CSR, A/O, A/A, C/A, LDO, Teller, Authority/Credit Committee/Board).
            -   Key Activities/Tasks: Describe the primary actions performed or responsibilities within that step.
            -   Documents/Outputs/Inputs (if applicable): Mention any important forms, reports, communications, or other relevant items that are generated, received, or used.
            -   Decision Points (if applicable): Note any critical junctures where a choice is made, a condition is met, or a process diverges.

            Present the summary as a numbered list, where each number corresponds to a distinct step in the sequence of the loan process. Under each numbered step, use bullet points to detail the involved components. The summary should accurately reflect the full sequential flow as described in the file.

            File Content:
            {file_content}
            """
        try:
            summary = call_gemini(summary_prompt, temperature=0.1, max_output_tokens=20000)
            # Remove any leading/trailing whitespace and ensure it's not too long
            return summary
        except Exception as e:
            logger.error(f"Error summarizing file content: {e}")
            return file_content[:1000] + "\n... (truncated)"

    def visualize(self, prompt: str, file_texts: list) -> dict:
        """
        Dedicated visualization service that generates BPMN diagrams from process descriptions.
        This service only handles visualization, not process improvement or bottleneck analysis.
        """
        # Detect language from user prompt
        detected_language = self._detect_language(prompt)
        logger.info(f"Detected language: {detected_language}")
        
        # Combine all file contents into a single string for context, using LLM summarization
        combined_file_content = ""
        for file_text in file_texts:
            # summarized_content = self._summarize_file_content(file_text['file_type'], file_text['file_content'], detected_language)
            combined_file_content += f"File Type: {file_text['file_type']}\n"
            combined_file_content += f"File Content:\n{file_text['file_content']}\n\n"
            # combined_file_content += f"File Summary:\n{summarized_content}\n"
        print("combined_file_content", combined_file_content)
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
            6. Các đường luồng thông điệp (Message Flows) để thể hiện sự trao đổi thông tin giữa các Pool hoặc Lane khác nhau, nếu có sự tương tác qua lại giữa chúng.
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
            6.  Message Flows (dashed arrows) to illustrate the exchange of information or communication between different Pools or Lanes, where interactions across participants occur.
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
        return {
            "diagram_data": """<?xml version="1.0" encoding="UTF-8"?>\n<bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">\n  <bpmn:collaboration id="Collaboration_1">\n    <bpmn:participant id="Participant_KhachHang" name="Khách hàng" processRef="Process_KhachHang" />\n    <bpmn:participant id="Participant_NganHang" name="Ngân hàng ACB – PGD Lê Đại Hành" processRef="Process_NganHang" />\n    <bpmn:messageFlow id="MessageFlow_1" sourceRef="Task_Customer_RequestLoan" targetRef="Task_PFC_FindCustomer" name="Yêu cầu vay vốn" />\n    <bpmn:messageFlow id="MessageFlow_2" sourceRef="Task_Customer_RequestEarlySettlement" targetRef="Task_CSR_ReceiveEarlyRequest" name="Gửi yêu cầu thanh lý trước hạn" />\n    <bpmn:messageFlow id="MessageFlow_3" sourceRef="Task_Customer_MakeFinalPayment" targetRef="Task_Teller_CollectPayment" name="Thanh toán dứt điểm" />\n    <bpmn:messageFlow id="MessageFlow_4" sourceRef="Task_Customer_RequestAssetRelease" targetRef="Task_CSR_ReceiveAssetReleaseRequest" name="Yêu cầu giải chấp tài sản" />\n    <bpmn:messageFlow id="MessageFlow_5" sourceRef="Task_LDO_PerformAssetRelease" targetRef="EndEvent_Customer_AssetReleased" name="Thông báo tài sản đã giải chấp" />\n  </bpmn:collaboration>\n  <bpmn:process id="Process_KhachHang" isExecutable="false">\n    <bpmn:startEvent id="StartEvent_Customer" name="Có nhu cầu vay vốn">\n      <bpmn:outgoing>SequenceFlow_1</bpmn:outgoing>\n    </bpmn:startEvent>\n    <bpmn:task id="Task_Customer_RequestLoan" name="Liên hệ ngân hàng yêu cầu vay vốn">\n      <bpmn:incoming>SequenceFlow_1</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_2</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:eventBasedGateway id="Gateway_Customer_PaymentDecision">\n      <bpmn:incoming>SequenceFlow_2</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_3</bpmn:outgoing>\n      <bpmn:outgoing>SequenceFlow_4</bpmn:outgoing>\n    </bpmn:eventBasedGateway>\n    <bpmn:intermediateCatchEvent id="Event_Customer_OnTimePayment">\n      <bpmn:incoming>SequenceFlow_3</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_5</bpmn:outgoing>\n      <bpmn:timerEventDefinition />\n    </bpmn:intermediateCatchEvent>\n    <bpmn:intermediateCatchEvent id="Event_Customer_EarlyPayment">\n      <bpmn:incoming>SequenceFlow_4</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_6</bpmn:outgoing>\n      <bpmn:messageEventDefinition />\n    </bpmn:intermediateCatchEvent>\n    <bpmn:task id="Task_Customer_MakeFinalPayment" name="Thực hiện thanh toán đúng hạn">\n      <bpmn:incoming>SequenceFlow_5</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_7</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_Customer_RequestEarlySettlement" name="Yêu cầu thanh lý khoản vay trước hạn">\n      <bpmn:incoming>SequenceFlow_6</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_8</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:endEvent id="EndEvent_Customer_EarlySettled" name="Khoản vay được tất toán trước hạn">\n      <bpmn:incoming>SequenceFlow_8</bpmn:incoming>\n    </bpmn:endEvent>\n    <bpmn:task id="Task_Customer_RequestAssetRelease" name="Đề nghị giải chấp tài sản đảm bảo">\n      <bpmn:incoming>SequenceFlow_7</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_9</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:endEvent id="EndEvent_Customer_AssetReleased" name="Nhận lại tài sản đã giải chấp">\n      <bpmn:incoming>SequenceFlow_9</bpmn:incoming>\n    </bpmn:endEvent>\n    <bpmn:sequenceFlow id="SequenceFlow_1" sourceRef="StartEvent_Customer" targetRef="Task_Customer_RequestLoan" />\n    <bpmn:sequenceFlow id="SequenceFlow_2" sourceRef="Task_Customer_RequestLoan" targetRef="Gateway_Customer_PaymentDecision" />\n    <bpmn:sequenceFlow id="SequenceFlow_3" sourceRef="Gateway_Customer_PaymentDecision" targetRef="Event_Customer_OnTimePayment" />\n    <bpmn:sequenceFlow id="SequenceFlow_4" sourceRef="Gateway_Customer_PaymentDecision" targetRef="Event_Customer_EarlyPayment" />\n    <bpmn:sequenceFlow id="SequenceFlow_5" sourceRef="Event_Customer_OnTimePayment" targetRef="Task_Customer_MakeFinalPayment" />\n    <bpmn:sequenceFlow id="SequenceFlow_6" sourceRef="Event_Customer_EarlyPayment" targetRef="Task_Customer_RequestEarlySettlement" />\n    <bpmn:sequenceFlow id="SequenceFlow_7" sourceRef="Task_Customer_MakeFinalPayment" targetRef="Task_Customer_RequestAssetRelease" />\n    <bpmn:sequenceFlow id="SequenceFlow_8" sourceRef="Task_Customer_RequestEarlySettlement" targetRef="EndEvent_Customer_EarlySettled" />\n    <bpmn:sequenceFlow id="SequenceFlow_9" sourceRef="Task_Customer_RequestAssetRelease" targetRef="EndEvent_Customer_AssetReleased" />\n  </bpmn:process>\n  <bpmn:process id="Process_NganHang" isExecutable="true">\n    <bpmn:laneSet id="LaneSet_NganHang">\n      <bpmn:lane id="Lane_PFC" name="PFC (Nhân viên phát triển khách hàng)">\n        <bpmn:flowNodeRef>Task_PFC_FindCustomer</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_PFC_IntroduceServices</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_PFC_NegotiateTerms</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>SubProcess_Approval</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>StartEvent_Bank</bpmn:flowNodeRef>\n      </bpmn:lane>\n      <bpmn:lane id="Lane_CSR" name="Loan CSR">\n        <bpmn:flowNodeRef>Task_CSR_ReceiveEarlyRequest</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_CSR_SubmitEarlyForApproval</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_CSR_CalculateFees</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_CSR_CheckPaymentHistory</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Gateway_CSR_AssetRelease</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_CSR_ReceiveAssetReleaseRequest</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_CSR_PrepareReleaseDocs</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Gateway_Bank_PaymentType</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>EndEvent_Bank_SettledNoRelease</bpmn:flowNodeRef>\n      </bpmn:lane>\n      <bpmn:lane id="Lane_Teller" name="Teller">\n        <bpmn:flowNodeRef>Task_Teller_SettleAccount</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_Teller_CollectPayment</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>EndEvent_Bank_EarlySettled</bpmn:flowNodeRef>\n      </bpmn:lane>\n      <bpmn:lane id="Lane_LDO" name="LDO">\n        <bpmn:flowNodeRef>Task_LDO_PerformAssetRelease</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>EndEvent_Bank_AssetReleased</bpmn:flowNodeRef>\n      </bpmn:lane>\n      <bpmn:lane id="Lane_Management" name="Cấp có thẩm quyền">\n        <bpmn:flowNodeRef>Task_Mgmt_ApproveEarlySettlement</bpmn:flowNodeRef>\n        <bpmn:flowNodeRef>Task_Mgmt_ApproveAssetRelease</bpmn:flowNodeRef>\n      </bpmn:lane>\n    </bpmn:laneSet>\n    <bpmn:task id="Task_PFC_FindCustomer" name="Tiếp nhận và tìm hiểu nhu cầu khách hàng">\n      <bpmn:incoming>SequenceFlow_10</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_11</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_PFC_IntroduceServices" name="Nghiên cứu và đánh giá sơ bộ khách hàng">\n      <bpmn:incoming>SequenceFlow_11</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_12</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_PFC_NegotiateTerms" name="Đàm phán sơ bộ điều kiện tín dụng">\n      <bpmn:incoming>SequenceFlow_12</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_13</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:subProcess id="SubProcess_Approval" name="Thực hiện các bước trung gian (2-15)">\n      <bpmn:incoming>SequenceFlow_13</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_14</bpmn:outgoing>\n    </bpmn:subProcess>\n    <bpmn:task id="Task_CSR_ReceiveEarlyRequest" name="Tiếp nhận yêu cầu thanh lý trước hạn">\n      <bpmn:incoming>SequenceFlow_16</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_18</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_CSR_SubmitEarlyForApproval" name="Trình cấp có thẩm quyền phê duyệt">\n      <bpmn:incoming>SequenceFlow_18</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_19</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_Mgmt_ApproveEarlySettlement" name="Xem xét và phê duyệt yêu cầu trả trước hạn">\n      <bpmn:incoming>SequenceFlow_19</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_20</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_CSR_CalculateFees" name="Tính toán và nhập lãi, phí phạt vào hệ thống">\n      <bpmn:incoming>SequenceFlow_20</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_21</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_Teller_SettleAccount" name="Thực hiện thanh lý tài khoản vay">\n      <bpmn:incoming>SequenceFlow_21</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_22</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_Teller_CollectPayment" name="Thu vốn, lãi, phí lần cuối">\n      <bpmn:incoming>SequenceFlow_17</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_23</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_CSR_CheckPaymentHistory" name="Kiểm tra quá trình thanh toán và xử lý tất toán">\n      <bpmn:incoming>SequenceFlow_23</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_24</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:exclusiveGateway id="Gateway_CSR_AssetRelease" name="Khách hàng có yêu cầu giải chấp tài sản?">\n      <bpmn:incoming>SequenceFlow_24</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_25</bpmn:outgoing>\n      <bpmn:outgoing>SequenceFlow_26</bpmn:outgoing>\n    </bpmn:exclusiveGateway>\n    <bpmn:task id="Task_CSR_ReceiveAssetReleaseRequest" name="Tiếp nhận và kiểm tra yêu cầu giải chấp">\n      <bpmn:incoming>SequenceFlow_26</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_28</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_CSR_PrepareReleaseDocs" name="Lập giấy đề nghị giải chấp trình duyệt">\n      <bpmn:incoming>SequenceFlow_28</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_29</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_Mgmt_ApproveAssetRelease" name="Ký duyệt đề nghị giải chấp tài sản">\n      <bpmn:incoming>SequenceFlow_29</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_30</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:task id="Task_LDO_PerformAssetRelease" name="Nhận đề nghị và làm thủ tục giải chấp">\n      <bpmn:incoming>SequenceFlow_30</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_31</bpmn:outgoing>\n    </bpmn:task>\n    <bpmn:startEvent id="StartEvent_Bank">\n      <bpmn:outgoing>SequenceFlow_10</bpmn:outgoing>\n    </bpmn:startEvent>\n    <bpmn:exclusiveGateway id="Gateway_Bank_PaymentType">\n      <bpmn:incoming>SequenceFlow_14</bpmn:incoming>\n      <bpmn:outgoing>SequenceFlow_16</bpmn:outgoing>\n      <bpmn:outgoing>SequenceFlow_17</bpmn:outgoing>\n    </bpmn:exclusiveGateway>\n    <bpmn:endEvent id="EndEvent_Bank_EarlySettled" name="Khoản vay đã tất toán trước hạn">\n      <bpmn:incoming>SequenceFlow_22</bpmn:incoming>\n    </bpmn:endEvent>\n    <bpmn:endEvent id="EndEvent_Bank_SettledNoRelease" name="Khoản vay đã tất toán">\n      <bpmn:incoming>SequenceFlow_25</bpmn:incoming>\n    </bpmn:endEvent>\n    <bpmn:endEvent id="EndEvent_Bank_AssetReleased" name="Hoàn tất giải chấp tài sản">\n      <bpmn:incoming>SequenceFlow_31</bpmn:incoming>\n    </bpmn:endEvent>\n    <bpmn:sequenceFlow id="SequenceFlow_10" sourceRef="StartEvent_Bank" targetRef="Task_PFC_FindCustomer" />\n    <bpmn:sequenceFlow id="SequenceFlow_11" sourceRef="Task_PFC_FindCustomer" targetRef="Task_PFC_IntroduceServices" />\n    <bpmn:sequenceFlow id="SequenceFlow_12" sourceRef="Task_PFC_IntroduceServices" targetRef="Task_PFC_NegotiateTerms" />\n    <bpmn:sequenceFlow id="SequenceFlow_13" sourceRef="Task_PFC_NegotiateTerms" targetRef="SubProcess_Approval" />\n    <bpmn:sequenceFlow id="SequenceFlow_14" sourceRef="SubProcess_Approval" targetRef="Gateway_Bank_PaymentType" />\n    <bpmn:sequenceFlow id="SequenceFlow_16" name="Thanh lý trước hạn" sourceRef="Gateway_Bank_PaymentType" targetRef="Task_CSR_ReceiveEarlyRequest" />\n    <bpmn:sequenceFlow id="SequenceFlow_17" name="Thanh lý đúng hạn" sourceRef="Gateway_Bank_PaymentType" targetRef="Task_Teller_CollectPayment" />\n    <bpmn:sequenceFlow id="SequenceFlow_18" sourceRef="Task_CSR_ReceiveEarlyRequest" targetRef="Task_CSR_SubmitEarlyForApproval" />\n    <bpmn:sequenceFlow id="SequenceFlow_19" sourceRef="Task_CSR_SubmitEarlyForApproval" targetRef="Task_Mgmt_ApproveEarlySettlement" />\n    <bpmn:sequenceFlow id="SequenceFlow_20" sourceRef="Task_Mgmt_ApproveEarlySettlement" targetRef="Task_CSR_CalculateFees" />\n    <bpmn:sequenceFlow id="SequenceFlow_21" sourceRef="Task_CSR_CalculateFees" targetRef="Task_Teller_SettleAccount" />\n    <bpmn:sequenceFlow id="SequenceFlow_22" sourceRef="Task_Teller_SettleAccount" targetRef="EndEvent_Bank_EarlySettled" />\n    <bpmn:sequenceFlow id="SequenceFlow_23" sourceRef="Task_Teller_CollectPayment" targetRef="Task_CSR_CheckPaymentHistory" />\n    <bpmn:sequenceFlow id="SequenceFlow_24" sourceRef="Task_CSR_CheckPaymentHistory" targetRef="Gateway_CSR_AssetRelease" />\n    <bpmn:sequenceFlow id="SequenceFlow_25" name="Không" sourceRef="Gateway_CSR_AssetRelease" targetRef="EndEvent_Bank_SettledNoRelease" />\n    <bpmn:sequenceFlow id="SequenceFlow_26" name="Có" sourceRef="Gateway_CSR_AssetRelease" targetRef="Task_CSR_ReceiveAssetReleaseRequest" />\n    <bpmn:sequenceFlow id="SequenceFlow_28" sourceRef="Task_CSR_ReceiveAssetReleaseRequest" targetRef="Task_CSR_PrepareReleaseDocs" />\n    <bpmn:sequenceFlow id="SequenceFlow_29" sourceRef="Task_CSR_PrepareReleaseDocs" targetRef="Task_Mgmt_ApproveAssetRelease" />\n    <bpmn:sequenceFlow id="SequenceFlow_30" sourceRef="Task_Mgmt_ApproveAssetRelease" targetRef="Task_LDO_PerformAssetRelease" />\n    <bpmn:sequenceFlow id="SequenceFlow_31" sourceRef="Task_LDO_PerformAssetRelease" targetRef="EndEvent_Bank_AssetReleased" />\n  </bpmn:process>\n  <bpmndi:BPMNDiagram id="BPMNDiagram_1">\n    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collaboration_1">\n      <bpmndi:BPMNShape id="Participant_KhachHang_di" bpmnElement="Participant_KhachHang" isHorizontal="true">\n        <dc:Bounds x="160" y="80" width="1840" height="250" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="StartEvent_Customer_di" bpmnElement="StartEvent_Customer">\n        <dc:Bounds x="212" y="162" width="36" height="36" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="194" y="205" width="73" height="27" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_Customer_RequestLoan_di" bpmnElement="Task_Customer_RequestLoan">\n        <dc:Bounds x="300" y="140" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Gateway_Customer_PaymentDecision_di" bpmnElement="Gateway_Customer_PaymentDecision">\n        <dc:Bounds x="455" y="155" width="50" height="50" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Event_Customer_OnTimePayment_di" bpmnElement="Event_Customer_OnTimePayment">\n        <dc:Bounds x="562" y="102" width="36" height="36" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Event_Customer_EarlyPayment_di" bpmnElement="Event_Customer_EarlyPayment">\n        <dc:Bounds x="562" y="222" width="36" height="36" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_Customer_MakeFinalPayment_di" bpmnElement="Task_Customer_MakeFinalPayment">\n        <dc:Bounds x="650" y="80" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_Customer_RequestEarlySettlement_di" bpmnElement="Task_Customer_RequestEarlySettlement">\n        <dc:Bounds x="650" y="200" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="EndEvent_Customer_EarlySettled_di" bpmnElement="EndEvent_Customer_EarlySettled">\n        <dc:Bounds x="812" y="222" width="36" height="36" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="788" y="265" width="85" height="40" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_Customer_RequestAssetRelease_di" bpmnElement="Task_Customer_RequestAssetRelease">\n        <dc:Bounds x="810" y="80" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="EndEvent_Customer_AssetReleased_di" bpmnElement="EndEvent_Customer_AssetReleased">\n        <dc:Bounds x="972" y="102" width="36" height="36" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="949" y="145" width="82" height="40" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNEdge id="SequenceFlow_1_di" bpmnElement="SequenceFlow_1">\n        <di:waypoint x="248" y="180" />\n        <di:waypoint x="300" y="180" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_2_di" bpmnElement="SequenceFlow_2">\n        <di:waypoint x="400" y="180" />\n        <di:waypoint x="455" y="180" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_3_di" bpmnElement="SequenceFlow_3">\n        <di:waypoint x="480" y="155" />\n        <di:waypoint x="480" y="120" />\n        <di:waypoint x="562" y="120" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_4_di" bpmnElement="SequenceFlow_4">\n        <di:waypoint x="480" y="205" />\n        <di:waypoint x="480" y="240" />\n        <di:waypoint x="562" y="240" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_5_di" bpmnElement="SequenceFlow_5">\n        <di:waypoint x="598" y="120" />\n        <di:waypoint x="650" y="120" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_6_di" bpmnElement="SequenceFlow_6">\n        <di:waypoint x="598" y="240" />\n        <di:waypoint x="650" y="240" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_7_di" bpmnElement="SequenceFlow_7">\n        <di:waypoint x="750" y="120" />\n        <di:waypoint x="810" y="120" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_8_di" bpmnElement="SequenceFlow_8">\n        <di:waypoint x="750" y="240" />\n        <di:waypoint x="812" y="240" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_9_di" bpmnElement="SequenceFlow_9">\n        <di:waypoint x="910" y="120" />\n        <di:waypoint x="972" y="120" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNShape id="Participant_NganHang_di" bpmnElement="Participant_NganHang" isHorizontal="true">\n        <dc:Bounds x="160" y="330" width="1840" height="650" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Lane_PFC_di" bpmnElement="Lane_PFC" isHorizontal="true">\n        <dc:Bounds x="190" y="330" width="1810" height="130" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_PFC_FindCustomer_di" bpmnElement="Task_PFC_FindCustomer">\n        <dc:Bounds x="300" y="355" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_PFC_IntroduceServices_di" bpmnElement="Task_PFC_IntroduceServices">\n        <dc:Bounds x="430" y="355" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_PFC_NegotiateTerms_di" bpmnElement="Task_PFC_NegotiateTerms">\n        <dc:Bounds x="560" y="355" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="SubProcess_Approval_di" bpmnElement="SubProcess_Approval" isExpanded="false">\n        <dc:Bounds x="690" y="355" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="StartEvent_Bank_di" bpmnElement="StartEvent_Bank">\n        <dc:Bounds x="222" y="377" width="36" height="36" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNEdge id="SequenceFlow_10_di" bpmnElement="SequenceFlow_10">\n        <di:waypoint x="258" y="395" />\n        <di:waypoint x="300" y="395" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_11_di" bpmnElement="SequenceFlow_11">\n        <di:waypoint x="400" y="395" />\n        <di:waypoint x="430" y="395" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_12_di" bpmnElement="SequenceFlow_12">\n        <di:waypoint x="530" y="395" />\n        <di:waypoint x="560" y="395" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_13_di" bpmnElement="SequenceFlow_13">\n        <di:waypoint x="660" y="395" />\n        <di:waypoint x="690" y="395" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNShape id="Lane_CSR_di" bpmnElement="Lane_CSR" isHorizontal="true">\n        <dc:Bounds x="190" y="460" width="1810" height="130" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_CSR_ReceiveEarlyRequest_di" bpmnElement="Task_CSR_ReceiveEarlyRequest">\n        <dc:Bounds x="930" y="485" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_CSR_SubmitEarlyForApproval_di" bpmnElement="Task_CSR_SubmitEarlyForApproval">\n        <dc:Bounds x="1060" y="485" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_CSR_CalculateFees_di" bpmnElement="Task_CSR_CalculateFees">\n        <dc:Bounds x="1320" y="485" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_CSR_CheckPaymentHistory_di" bpmnElement="Task_CSR_CheckPaymentHistory">\n        <dc:Bounds x="1060" y="485" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Gateway_CSR_AssetRelease_di" bpmnElement="Gateway_CSR_AssetRelease" isMarkerVisible="true">\n        <dc:Bounds x="1195" y="510" width="50" height="50" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="1177" y="567" width="87" height="40" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_CSR_ReceiveAssetReleaseRequest_di" bpmnElement="Task_CSR_ReceiveAssetReleaseRequest">\n        <dc:Bounds x="1320" y="485" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_CSR_PrepareReleaseDocs_di" bpmnElement="Task_CSR_PrepareReleaseDocs">\n        <dc:Bounds x="1450" y="485" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="ExclusiveGateway_1l2gejk_di" bpmnElement="Gateway_Bank_PaymentType" isMarkerVisible="true">\n        <dc:Bounds x="825" y="510" width="50" height="50" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNEdge id="SequenceFlow_14_di" bpmnElement="SequenceFlow_14">\n        <di:waypoint x="790" y="395" />\n        <di:waypoint x="850" y="395" />\n        <di:waypoint x="850" y="510" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_18_di" bpmnElement="SequenceFlow_18">\n        <di:waypoint x="1030" y="525" />\n        <di:waypoint x="1060" y="525" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_23_di" bpmnElement="SequenceFlow_23">\n        <di:waypoint x="1010" y="665" />\n        <di:waypoint x="1010" y="525" />\n        <di:waypoint x="1060" y="525" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_24_di" bpmnElement="SequenceFlow_24">\n        <di:waypoint x="1160" y="525" />\n        <di:waypoint x="1195" y="525" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_26_di" bpmnElement="SequenceFlow_26">\n        <di:waypoint x="1245" y="525" />\n        <di:waypoint x="1320" y="525" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="1279" y="507" width="18" height="14" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_28_di" bpmnElement="SequenceFlow_28">\n        <di:waypoint x="1420" y="525" />\n        <di:waypoint x="1450" y="525" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNShape id="Lane_Teller_di" bpmnElement="Lane_Teller" isHorizontal="true">\n        <dc:Bounds x="190" y="590" width="1810" height="130" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_Teller_SettleAccount_di" bpmnElement="Task_Teller_SettleAccount">\n        <dc:Bounds x="1450" y="625" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_Teller_CollectPayment_di" bpmnElement="Task_Teller_CollectPayment">\n        <dc:Bounds x="960" y="625" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNEdge id="SequenceFlow_17_di" bpmnElement="SequenceFlow_17">\n        <di:waypoint x="850" y="560" />\n        <di:waypoint x="850" y="665" />\n        <di:waypoint x="960" y="665" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="859" y="633" width="82" height="14" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_21_di" bpmnElement="SequenceFlow_21">\n        <di:waypoint x="1420" y="525" />\n        <di:waypoint x="1500" y="525" />\n        <di:waypoint x="1500" y="625" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNShape id="EndEvent_Bank_EarlySettled_di" bpmnElement="EndEvent_Bank_EarlySettled">\n        <dc:Bounds x="1582" y="647" width="36" height="36" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="1558" y="690" width="85" height="40" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNEdge id="SequenceFlow_22_di" bpmnElement="SequenceFlow_22">\n        <di:waypoint x="1550" y="665" />\n        <di:waypoint x="1582" y="665" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNShape id="Lane_LDO_di" bpmnElement="Lane_LDO" isHorizontal="true">\n        <dc:Bounds x="190" y="720" width="1810" height="130" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_LDO_PerformAssetRelease_di" bpmnElement="Task_LDO_PerformAssetRelease">\n        <dc:Bounds x="1700" y="745" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="EndEvent_Bank_AssetReleased_di" bpmnElement="EndEvent_Bank_AssetReleased">\n        <dc:Bounds x="1832" y="767" width="36" height="36" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="1812" y="810" width="77" height="27" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNEdge id="SequenceFlow_31_di" bpmnElement="SequenceFlow_31">\n        <di:waypoint x="1800" y="785" />\n        <di:waypoint x="1832" y="785" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNShape id="Lane_Management_di" bpmnElement="Lane_Management" isHorizontal="true">\n        <dc:Bounds x="190" y="850" width="1810" height="130" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_Mgmt_ApproveEarlySettlement_di" bpmnElement="Task_Mgmt_ApproveEarlySettlement">\n        <dc:Bounds x="1190" y="875" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNShape id="Task_Mgmt_ApproveAssetRelease_di" bpmnElement="Task_Mgmt_ApproveAssetRelease">\n        <dc:Bounds x="1570" y="875" width="100" height="80" />\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNEdge id="SequenceFlow_16_di" bpmnElement="SequenceFlow_16">\n        <di:waypoint x="875" y="535" />\n        <di:waypoint x="930" y="535" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="864" y="508" width="82" height="14" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_19_di" bpmnElement="SequenceFlow_19">\n        <di:waypoint x="1110" y="565" />\n        <di:waypoint x="1110" y="915" />\n        <di:waypoint x="1190" y="915" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_20_di" bpmnElement="SequenceFlow_20">\n        <di:waypoint x="1290" y="915" />\n        <di:waypoint x="1370" y="915" />\n        <di:waypoint x="1370" y="565" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNShape id="EndEvent_Bank_SettledNoRelease_di" bpmnElement="EndEvent_Bank_SettledNoRelease">\n        <dc:Bounds x="1202" y="647" width="36" height="36" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="1182" y="690" width="77" height="27" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNShape>\n      <bpmndi:BPMNEdge id="SequenceFlow_25_di" bpmnElement="SequenceFlow_25">\n        <di:waypoint x="1220" y="560" />\n        <di:waypoint x="1220" y="647" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="1226" y="596" width="38" height="14" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_29_di" bpmnElement="SequenceFlow_29">\n        <di:waypoint x="1500" y="565" />\n        <di:waypoint x="1500" y="915" />\n        <di:waypoint x="1570" y="915" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="SequenceFlow_30_di" bpmnElement="SequenceFlow_30">\n        <di:waypoint x="1670" y="915" />\n        <di:waypoint x="1750" y="915" />\n        <di:waypoint x="1750" y="825" />\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="MessageFlow_1_di" bpmnElement="MessageFlow_1">\n        <di:waypoint x="350" y="220" />\n        <di:waypoint x="350" y="355" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="354" y="280" width="72" height="14" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="MessageFlow_2_di" bpmnElement="MessageFlow_2">\n        <di:waypoint x="700" y="280" />\n        <di:waypoint x="700" y="525" />\n        <di:waypoint x="930" y="525" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="710" y="423" width="80" height="40" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="MessageFlow_3_di" bpmnElement="MessageFlow_3">\n        <di:waypoint x="700" y="160" />\n        <di:waypoint x="700" y="665" />\n        <di:waypoint x="960" y="665" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="799" y="638" width="82" height="14" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="MessageFlow_4_di" bpmnElement="MessageFlow_4">\n        <di:waypoint x="860" y="160" />\n        <di:waypoint x="860" y="525" />\n        <di:waypoint x="1320" y="525" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="1016" y="498" width="87" height="27" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n      <bpmndi:BPMNEdge id="MessageFlow_5_di" bpmnElement="MessageFlow_5">\n        <di:waypoint x="1750" y="745" />\n        <di:waypoint x="1750" y="120" />\n        <di:waypoint x="1008" y="120" />\n        <bpmndi:BPMNLabel>\n          <dc:Bounds x="1294" y="93" width="82" height="40" />\n        </bpmndi:BPMNLabel>\n      </bpmndi:BPMNEdge>\n    </bpmndi:BPMNPlane>\n  </bpmndi:BPMNDiagram>\n</bpmn:definitions>""",
            "diagram_name": "Quy trình cho vay tại ACB",
            "Diagram_description": "Sơ đồ này mô tả quy trình cho vay tại ngân hàng ACB, từ khâu tìm kiếm khách hàng đến khi tất toán khoản vay. Quy trình bao gồm các vai trò như Khách hàng, PFC, Teller, Loan CSR, LDO và Cấp có thẩm quyền, đồng thời phân nhánh xử lý cho các trường hợp thanh lý đúng hạn, trước hạn và có yêu cầu giải chấp tài sản.",
            "detail_descriptions": {'Liên hệ ngân hàng yêu cầu vay vốn': 'Khách hàng có nhu cầu vay vốn và chủ động liên hệ với ngân hàng để bắt đầu quy trình.', 'Tiếp nhận và tìm hiểu nhu cầu khách hàng': 'Nhân viên PFC tiếp nhận yêu cầu, giao tiếp với khách hàng mới và tìm hiểu nhu cầu vốn cũng như uy tín của khách hàng.', 'Nghiên cứu và đánh giá sơ bộ khách hàng': 'PFC nghiên cứu thực lực tài chính, triển vọng phát triển và những khó khăn hiện tại của khách hàng.', 'Đàm phán sơ bộ điều kiện tín dụng': 'PFC tiến hành đàm phán sơ bộ với khách hàng về các điều kiện cơ bản như lãi suất, thời hạn, phương thức cho vay.', 'Thực hiện các bước trung gian (2-15)': 'Đây là một quy trình con, đại diện cho các bước không được mô tả chi tiết trong tài liệu, bao gồm thẩm định, phê duyệt, và giải ngân khoản vay.', 'Thực hiện thanh toán đúng hạn': 'Khi đến hạn, khách hàng thực hiện thanh toán đầy đủ vốn, lãi và các chi phí liên quan cho ngân hàng.', 'Yêu cầu thanh lý khoản vay trước hạn': 'Khách hàng có nhu cầu tất toán khoản vay trước thời hạn quy định trong hợp đồng và gửi đơn yêu cầu cho ngân hàng.', 'Thu vốn, lãi, phí lần cuối': 'Teller thu các khoản thanh toán cuối cùng từ khách hàng trên tài khoản vay.', 'Kiểm tra quá trình thanh toán và xử lý tất toán': 'Loan CSR kiểm tra lại toàn bộ lịch sử thanh toán, số dư vốn, lãi, phí để xác định xử lý tất toán khoản vay.', 'Tiếp nhận yêu cầu thanh lý trước hạn': 'Loan CSR tiếp nhận đơn yêu cầu thanh lý trước hạn từ khách hàng.', 'Trình cấp có thẩm quyền phê duyệt': 'Loan CSR trình yêu cầu thanh lý trước hạn lên cấp có thẩm quyền để xem xét và phê duyệt.', 'Xem xét và phê duyệt yêu cầu trả trước hạn': 'Cấp có thẩm quyền xem xét và đưa ra quyết định phê duyệt hoặc từ chối yêu cầu thanh lý trước hạn.', 'Tính toán và nhập lãi, phí phạt vào hệ thống': 'Sau khi được duyệt, Loan CSR tính toán các khoản phí, lãi phạt (nếu có) và cập nhật vào hệ thống TCBS.', 'Thực hiện thanh lý tài khoản vay': 'Teller thực hiện thao tác cuối cùng để tất toán tài khoản vay trên hệ thống.', 'Đề nghị giải chấp tài sản đảm bảo': 'Sau khi hoàn tất nghĩa vụ trả nợ, khách hàng gửi yêu cầu giải chấp tài sản đã thế chấp.', 'Tiếp nhận và kiểm tra yêu cầu giải chấp': 'Loan CSR tiếp nhận yêu cầu, kiểm tra các dư nợ còn lại của khách hàng (nếu có).', 'Lập giấy đề nghị giải chấp trình duyệt': 'Loan CSR chuẩn bị hồ sơ, lập giấy đề nghị giải chấp theo mẫu và trình lên cấp có thẩm quyền.', 'Ký duyệt đề nghị giải chấp tài sản': 'Cấp có thẩm quyền xem xét và ký duyệt vào giấy đề nghị giải chấp.', 'Nhận đề nghị và làm thủ tục giải chấp': 'LDO (Loan Documentation Officer) nhận đề nghị đã được duyệt và tiến hành các thủ tục cần thiết để giải chấp tài sản cho khách hàng.'},
            "Memory": "Diagram: Quy trình cho vay tại ACB Diagram; Tasks: 19; File type(s): docx; Preferences: standard; Language: english."
        }
        # try:
        #     response = call_gemini(visualization_prompt, temperature=0.2, max_output_tokens=20000)
        #     logger.info(f"Visualization_prompt: {visualization_prompt}")
        #     logger.info(f"Raw LLM response: {response}")
            
        #     # Try to extract JSON from the response
        #     import json
            
        #     # Look for JSON in the response
        #     json_match = re.search(r'\{.*\}', response, re.DOTALL)
        #     if json_match:
        #         response_json = json.loads(json_match.group())
                
        #         # Generate concise memory focusing on user preferences and diagram data
        #         file_types = ', '.join([ft['file_type'] for ft in file_texts])
        #         num_tasks = len(response_json.get("detail_descriptions", {}))
        #         diagram_name = response_json.get("diagram_name", "N/A")
        #         # Heuristic: extract special preferences from prompt
        #         preferences = []
        #         prompt_lower = prompt.lower()
        #         if "swimlane" in prompt_lower or "swim lane" in prompt_lower:
        #             preferences.append("swimlane")
        #         if "highlight" in prompt_lower or "làm nổi bật" in prompt_lower:
        #             preferences.append("highlighted steps")
        #         if "approval" in prompt_lower or "phê duyệt" in prompt_lower:
        #             preferences.append("approval steps")
        #         if "color" in prompt_lower or "màu" in prompt_lower:
        #             preferences.append("color coding")
        #         if not preferences:
        #             preferences.append("standard")
                
        #         # Add language to memory for session consistency
        #         memory_content = (
        #             f"Diagram: {diagram_name}; Tasks: {num_tasks}; File type(s): {file_types}; "
        #             f"Preferences: {', '.join(preferences)}; Language: {detected_language}."
        #         )
        #         return {
        #             "diagram_data": response_json.get("diagram_data", "<bpmn:definitions>...</bpmn:definitions>"),
        #             "diagram_name": response_json.get("diagram_name", "Process Diagram"),
        #             "Diagram_description": response_json.get("diagram_description", "Generated BPMN diagram"),
        #             "detail_descriptions": response_json.get("detail_descriptions", {}),
        #             "Memory": memory_content.strip()
        #         }
        #     else:
        #         # Fallback if JSON parsing fails
        #         logger.warning("Could not parse JSON from LLM response, using fallback")
        #         file_types = ', '.join([ft['file_type'] for ft in file_texts])
        #         preferences = []
        #         prompt_lower = prompt.lower()
        #         if "swimlane" in prompt_lower or "swim lane" in prompt_lower:
        #             preferences.append("swimlane")
        #         if "highlight" in prompt_lower or "làm nổi bật" in prompt_lower:
        #             preferences.append("highlighted steps")
        #         if "approval" in prompt_lower or "phê duyệt" in prompt_lower:
        #             preferences.append("approval steps")
        #         if "color" in prompt_lower or "màu" in prompt_lower:
        #             preferences.append("color coding")
        #         if not preferences:
        #             preferences.append("standard")
                
        #         fallback_memory = (
        #             f"Diagram: Generated Process Diagram; Tasks: 2; File type(s): {file_types}; "
        #             f"Preferences: {', '.join(preferences)}; Language: {detected_language}."
        #         )
        #         return {
        #             "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
        #             "diagram_name": "Generated Process Diagram",
        #             "Diagram_description": "BPMN diagram generated from process description",
        #             "detail_descriptions": {"Task_1": "Process step 1", "Task_2": "Process step 2"},
        #             "Memory": fallback_memory.strip()
        #         }
                
        # except Exception as e:
        #     logger.error(f"Error in visualization service: {e}")
        #     error_memory = (
        #         f"Diagram: Error - Process Diagram; Tasks: 0; File type(s): {', '.join([ft['file_type'] for ft in file_texts])}; "
        #         f"Preferences: error; Language: {detected_language}."
        #     )
        #     # Return a basic fallback response
        #     return {
        #         "diagram_data": "<bpmn:definitions>...</bpmn:definitions>",
        #         "diagram_name": "Error - Process Diagram",
        #         "Diagram_description": "Error occurred during diagram generation",
        #         "detail_descriptions": {"Error": "Could not generate diagram"},
        #         "Memory": error_memory.strip()
        #     }