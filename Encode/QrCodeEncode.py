import qrcode
import cv2
import os
import shutil
#需要传输的数据
data = '''It has infected thousands of people, closed borders and put parts of China into lockdown. But the virus causing the outbreak of illness does not yet have a proper name. It has been referred to as the coronavirus. But that is the name of the group of viruses it belongs to. It has also been given the temporary title 2019-nCoV. But just saying that is a mouthful. A group of scientists has been grappling behind closed doors to find a proper term. So why has it taken so long?
"The naming of a new virus is often quite delayed and the focus until now has been on the public health response, which is understandable," says Crystal Watson, senior scholar and assistant professor at the Johns Hopkins Center for Health Security. "But there are reasons the naming should be a priority." To try to distinguish this particular virus, scientists have been calling it the novel or new coronavirus. Coronaviruses are named for their crown-like spikes when viewed through a microscope.
The World Health Organization (WHO) has recommended the temporary name 2019-nCoV, which includes the year it was discovered, "n" to denote new or novel, and "CoV" for coronavirus. But it has not exactly stuck. "The danger when you don't have an official name is that people start using terms like China Virus, and that can create a backlash against certain populations." With social media, unofficial names take hold quickly and are hard to take back, she says.
The urgent task of formally naming the virus is the responsibility of the International Committee on Taxonomy of Viruses (ICTV). Previous outbreaks provide cautionary tales for the team. The H1N1 virus in 2009 was dubbed "swine flu". This led Egypt to slaughter all of its pigs, even though it was spread by people, not pigs. According to these, the name for the new coronavirus should not include:
1) Geographical locations
2) People's names
3) The name of an animal or a kind of food 4) References to a particular culture or industry
It says the name should be short and descriptive - such as Sars (Severe Acute Respiratory Syndrome).
But for the name to stick it also needs a hook, says Benjamin Neuman, a professor of virology . "It has to roll off the tongue a little faster than the other names out there." The team began discussing a name about two weeks ago and took two days to settle on one, says Prof Neuman, who is chair of Biological Sciences at Texas A&M University-Texarkana in the US.
They are now submitting the name to a scientific journal for publication and hope to announce it within days. As well as helping the public understand the virus, the ICTV hopes it will allow researchers to focus on fighting it by saving time and confusion. "We will find out in the future whether we got it right," says Prof Neuman. "For someone like me, helping to name an important virus may ultimately end up being longer-lasting and more helpful than a career's worth of work. It's a big responsibility."'''
batch_size = 213#每张二维码容量(单位：B)
video = cv2.VideoWriter("output.mp4",
                        cv2.VideoWriter_fourcc('D','I','V','X'),
                        30,#FPS
                        (650,650))#视频格式
#img = qrcode.make('https://github.com')
qr = qrcode.QRCode(version = 10,#第2版本
                   error_correction = qrcode.constants.ERROR_CORRECT_M,#纠错能力为L
                   box_size = 10,
                   border = 4)#此配置一张二维码容量刚好为32B
index=0
#生成二维码函数
def summon_pic(qr, data, index):
    print(data)
    qr.clear()#清除数据
    qr.add_data(data)#加入数据
    qr.make()
    img=qr.make_image()#生成图像
    img.save("frames\\"+str(index)+'.jpg')
#清空文件夹
shutil.rmtree("frames", True)
os.mkdir("frames")
#生成所有的二维码
while len(data) > batch_size:
    batch_data = data[:batch_size]#截取前batch_size个字节
    data = data[batch_size:]#剩余字节
    summon_pic(qr, batch_data, index)
    index+=1
summon_pic(qr, data, index)
index+=1
#将生成二维码转成视频以用手机拍摄
for i in range(index):
    frame=cv2.imread("frames\\"+str(i)+'.jpg')
    print(i)
    for j in range(6):
        print("write"+str(j))
        video.write(frame)
video.release()